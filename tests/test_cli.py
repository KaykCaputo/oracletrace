import json
import importlib
import sys
from pathlib import Path
from oracletrace.tracer import TracerData, FunctionData, TracerMetadata, FunctionData
from oracletrace.compare import ComparisonData
from dataclasses import asdict
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.modules.pop("oracletrace.cli", None)
sys.modules.pop("oracletrace", None)
cli = importlib.import_module("oracletrace.cli")
assert str(REPO_ROOT / "oracletrace") in str(Path(cli.__file__).resolve())


def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError

@pytest.fixture
def trace_data() -> TracerData:
    return TracerData(
        metadata = TracerMetadata(
            total_execution_time = 5.033,
            total_functions = 2,
            root_path = str(REPO_ROOT) 
        ),
        functions = [
            FunctionData(
                name="foo",
                total_time=2.0,
                call_count=1,
                avg_time=2.0,
                callees=set(),
            ),
            FunctionData(
                name="bar",
                total_time=2.0,
                call_count=2,
                avg_time=1.0,
                callees=set()
            )
        ]
    )

@pytest.fixture
def baseline_trace_data() -> TracerData:
    return TracerData(
        metadata = TracerMetadata(
            total_execution_time = 3.5,
            total_functions = 2,
            root_path = str(REPO_ROOT) 
        ),
        functions = [
            FunctionData(
                name = "foo",
                total_time = 1.5,
                call_count = 3,
                avg_time = 0.5,
                callees=set()
            ),
            FunctionData(
                name = "bar",
                total_time = 2.0,
                call_count = 2,
                avg_time = 1.0,
                callees=set()
            )
        ]
    )
    
@pytest.fixture
def empty_trace_data() -> TracerData:
    return TracerData(
        metadata = TracerMetadata(
            total_execution_time = 0.0,
            total_functions = 0,
            root_path = str(REPO_ROOT)
        ),
        functions = []
    )

class FakeTracer:
    def __init__(self, root, ignore_patterns, data):
        self.root = root
        self.ignore_patterns = ignore_patterns
        self.data = data
        self.started = False
        self.stopped = False
        self.show_results_calls = []

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def get_trace_data(self):
        return self.data

    def show_results(self, top):
        self.show_results_calls.append(top)


def _run_cli(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", argv)
    return cli.main()


def test_main_returns_1_when_target_not_found(monkeypatch, capsys):
    exit_code = _run_cli(monkeypatch, ["oracletrace", "missing_script.py"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Target not found: missing_script.py" in captured.err


def test_main_returns_1_when_ignore_regex_is_invalid(monkeypatch, tmp_path, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('ok')\n", encoding="utf-8")

    exit_code = _run_cli(monkeypatch, ["oracletrace", str(target), "--ignore", "["])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Regex error: [" in captured.err


def test_main_runs_trace_and_exports_json_and_csv(monkeypatch, tmp_path, trace_data):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")
    json_output = tmp_path / "trace.json"
    csv_output = tmp_path / "trace.csv"

    fake_tracer_holder = {}

    def tracer_factory(root, ignore_patterns):
        fake = FakeTracer(root, ignore_patterns, trace_data)
        fake_tracer_holder["instance"] = fake
        return fake

    run_path_calls = []

    def fake_run_path(path, run_name):
        run_path_calls.append((path, run_name))

    monkeypatch.setattr(cli, "Tracer", tracer_factory)
    monkeypatch.setattr(cli.runpy, "run_path", fake_run_path)
    monkeypatch.setattr(sys, "path", sys.path.copy())

    exit_code = _run_cli(
        monkeypatch,
        [
            "oracletrace",
            str(target),
            "--json",
            str(json_output),
            "--csv",
            str(csv_output),
            "--ignore",
            r".*target.py:foo",
        ],
    )

    fake_tracer = fake_tracer_holder["instance"]

    assert exit_code == 0
    assert fake_tracer.started is True
    assert fake_tracer.stopped is True
    assert fake_tracer.show_results_calls == [None]
    assert run_path_calls == [(str(target.resolve()), "__main__")]

    loaded_json = json.loads(json_output.read_text(encoding="utf-8"))
    assert TracerData.from_dict(loaded_json) == trace_data

    csv_text = csv_output.read_text(encoding="utf-8")
    assert "function,total_time,calls,avg_time" in csv_text
    assert "foo,2.0,1,2.0" in csv_text
    assert "bar,2.0,2,1.0" in csv_text

    assert sys.path[0] == str(target.parent.resolve())


def test_main_exports_markdown(monkeypatch, tmp_path, trace_data):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")
    md_output = tmp_path / "report.md"

    monkeypatch.setattr(cli, "Tracer", lambda root, ignore_patterns: FakeTracer(root, ignore_patterns, trace_data))
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    exit_code = _run_cli(
        monkeypatch,
        ["oracletrace", str(target), "--markdown", str(md_output)],
    )

    assert exit_code == 0
    content = md_output.read_text(encoding="utf-8")
    assert content.startswith("## ⚡ OracleTrace Performance Report")
    assert "foo" in content


def test_main_markdown_includes_comparison(monkeypatch, tmp_path, trace_data, baseline_trace_data):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")
    compare_file = tmp_path / "baseline.json"
    compare_file.write_text(json.dumps(asdict(baseline_trace_data), default=set_default), encoding="utf-8")
    md_output = tmp_path / "report.md"

    monkeypatch.setattr(cli, "Tracer", lambda root, ignore_patterns: FakeTracer(root, ignore_patterns, trace_data))
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    exit_code = _run_cli(
        monkeypatch,
        ["oracletrace", str(target), "--compare", str(compare_file), "--markdown", str(md_output)],
    )

    assert exit_code == 0
    content = md_output.read_text(encoding="utf-8")
    # foo went 1.5s -> 2.0s, a regression, so the comparison section renders
    assert "### Comparison vs. baseline" in content
    assert "🔴" in content


def test_main_passes_top_value_to_show_results(monkeypatch, tmp_path, trace_data):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    fake_tracer_holder = {}

    def tracer_factory(root, ignore_patterns):
        fake = FakeTracer(root, ignore_patterns, trace_data)
        fake_tracer_holder["instance"] = fake
        return fake

    monkeypatch.setattr(cli, "Tracer", tracer_factory)
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    exit_code = _run_cli(monkeypatch, ["oracletrace", str(target), "--top", "5"])

    fake_tracer = fake_tracer_holder["instance"]
    assert exit_code == 0
    assert fake_tracer.show_results_calls == [5]


def test_main_passes_multidigit_top_value(monkeypatch, tmp_path, trace_data):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    fake_tracer_holder = {}

    def tracer_factory(root, ignore_patterns):
        fake = FakeTracer(root, ignore_patterns, trace_data)
        fake_tracer_holder["instance"] = fake
        return fake

    monkeypatch.setattr(cli, "Tracer", tracer_factory)
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    exit_code = _run_cli(monkeypatch, ["oracletrace", str(target), "--top", "10"])

    fake_tracer = fake_tracer_holder["instance"]
    assert exit_code == 0
    assert fake_tracer.show_results_calls == [10]


def test_main_rejects_zero_top(monkeypatch, tmp_path, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    exit_code = _run_cli(monkeypatch, ["oracletrace", str(target), "--top", "0"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "argument --top: invalid int value" in captured.err


def test_main_rejects_negative_top(monkeypatch, tmp_path, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    exit_code = _run_cli(monkeypatch, ["oracletrace", str(target), "--top", "-5"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "argument --top: invalid int value" in captured.err


def test_main_rejects_non_integer_top(monkeypatch, tmp_path, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    exit_code = _run_cli(monkeypatch, ["oracletrace", str(target), "--top", "foo"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "invalid int value" in captured.err


def test_main_rejects_float_top(monkeypatch, tmp_path, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    exit_code = _run_cli(monkeypatch, ["oracletrace", str(target), "--top", "3.5"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "invalid int value" in captured.err


def test_main_rejects_empty_top(monkeypatch, tmp_path, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    exit_code = _run_cli(monkeypatch, ["oracletrace", str(target), "--top", ""])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "invalid int value" in captured.err


def test_main_accepts_top_with_whitespace(monkeypatch, tmp_path, trace_data):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    fake_tracer_holder = {}

    def tracer_factory(root, ignore_patterns):
        fake = FakeTracer(root, ignore_patterns, trace_data)
        fake_tracer_holder["instance"] = fake
        return fake

    monkeypatch.setattr(cli, "Tracer", tracer_factory)
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    exit_code = _run_cli(monkeypatch, ["oracletrace", str(target), "--top", " 5 "])

    fake_tracer = fake_tracer_holder["instance"]
    assert exit_code == 0
    assert fake_tracer.show_results_calls == [5]


def test_main_accepts_large_top_value(monkeypatch, tmp_path, trace_data):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    fake_tracer_holder = {}

    def tracer_factory(root, ignore_patterns):
        fake = FakeTracer(root, ignore_patterns, trace_data)
        fake_tracer_holder["instance"] = fake
        return fake

    monkeypatch.setattr(cli, "Tracer", tracer_factory)
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    exit_code = _run_cli(monkeypatch, ["oracletrace", str(target), "--top", "99999"])

    fake_tracer = fake_tracer_holder["instance"]
    assert exit_code == 0
    assert fake_tracer.show_results_calls == [99999]


def test_main_rejects_zero_repeat(monkeypatch, tmp_path, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    exit_code = _run_cli(monkeypatch, ["oracletrace", str(target), "--repeat", "0"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "argument --repeat: invalid int value" in captured.err


def test_main_rejects_negative_repeat(monkeypatch, tmp_path, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    exit_code = _run_cli(monkeypatch, ["oracletrace", str(target), "--repeat", "-1"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "argument --repeat: invalid int value" in captured.err


def test_main_rejects_non_integer_repeat(monkeypatch, tmp_path, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    exit_code = _run_cli(monkeypatch, ["oracletrace", str(target), "--repeat", "abc"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "argument --repeat: invalid int value" in captured.err


def test_main_returns_1_when_compare_file_not_found(monkeypatch, tmp_path, trace_data, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    monkeypatch.setattr(cli, "Tracer", lambda root, ignore_patterns: FakeTracer(root, ignore_patterns, trace_data))
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    exit_code = _run_cli(
        monkeypatch,
        ["oracletrace", str(target), "--compare", str(tmp_path / "missing_compare.json")],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Compare file not found:" in captured.err


def test_main_returns_1_when_compare_file_has_invalid_json(monkeypatch, tmp_path, trace_data, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")
    compare_file = tmp_path / "baseline.json"
    compare_file.write_text("{invalid json", encoding="utf-8")

    monkeypatch.setattr(cli, "Tracer", lambda root, ignore_patterns: FakeTracer(root, ignore_patterns, trace_data))
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    exit_code = _run_cli(
        monkeypatch,
        ["oracletrace", str(target), "--compare", str(compare_file)],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Compare file contains invalid JSON:" in captured.err


def test_main_returns_1_when_compare_file_has_invalid_schema(monkeypatch, tmp_path, trace_data, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")
    compare_file = tmp_path / "baseline.json"
    compare_file.write_text('{"foo": "bar"}', encoding="utf-8")

    monkeypatch.setattr(cli, "Tracer", lambda root, ignore_patterns: FakeTracer(root, ignore_patterns, trace_data))
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    exit_code = _run_cli(
        monkeypatch,
        ["oracletrace", str(target), "--compare", str(compare_file)],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Compare file has invalid schema:" in captured.err


def test_main_returns_1_when_compare_file_empty(monkeypatch, tmp_path, trace_data, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")
    compare_file = tmp_path / "baseline.json"
    compare_file.write_text("", encoding="utf-8")

    monkeypatch.setattr(cli, "Tracer", lambda root, ignore_patterns: FakeTracer(root, ignore_patterns, trace_data))
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    exit_code = _run_cli(
        monkeypatch,
        ["oracletrace", str(target), "--compare", str(compare_file)],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Compare file contains invalid JSON" in captured.err


def test_main_fails_with_exit_2_on_regression(monkeypatch, tmp_path, empty_trace_data, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")
    compare_file = tmp_path / "baseline.json"
    compare_file.write_text(json.dumps(asdict(empty_trace_data), default=set_default), encoding="utf-8")

    monkeypatch.setattr(cli, "Tracer", lambda root, ignore_patterns: FakeTracer(root, ignore_patterns, empty_trace_data))
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    compare_calls = []

    def fake_compare_traces(old_data, new_data, threshold):
        compare_calls.append((old_data, new_data, threshold))
        return ComparisonData(
            deltas=[], regressions=[], improvements=[],
            new_functions=[], removed_functions=[],
            threshold=threshold, has_regression=True,
        )

    monkeypatch.setattr(cli, "compare_traces", fake_compare_traces)

    exit_code = _run_cli(
        monkeypatch,
        [
            "oracletrace",
            str(target),
            "--compare",
            str(compare_file),
            "--fail-on-regression",
            "--threshold",
            "7.5",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Build failed: performance regression above 7.50% detected." in captured.err
    assert compare_calls[0][2] == 7.5


def test_main_returns_0_when_no_regression(monkeypatch, tmp_path, trace_data):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")
    compare_file = tmp_path / "baseline.json"
    compare_file.write_text(json.dumps(asdict(trace_data), default=set_default), encoding="utf-8")

    monkeypatch.setattr(cli, "Tracer", lambda root, ignore_patterns: FakeTracer(root, ignore_patterns, trace_data))
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        cli,
        "compare_traces",
        lambda old_data, new_data, threshold: ComparisonData(
            deltas=[], regressions=[], improvements=[],
            new_functions=[], removed_functions=[],
            threshold=threshold, has_regression=False,
        )
    )

    exit_code = _run_cli(
        monkeypatch,
        [
            "oracletrace",
            str(target),
            "--compare",
            str(compare_file),
            "--fail-on-regression",
        ],
    )

    assert exit_code == 0

def test_main_shows_only_regressions(monkeypatch, tmp_path, trace_data, baseline_trace_data, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")
    compare_file = tmp_path / "baseline.json"
    compare_file.write_text(json.dumps(asdict(baseline_trace_data), default=set_default), encoding="utf-8")
    
    monkeypatch.setattr(cli, "Tracer", lambda root, ignore_patterns: FakeTracer(root, ignore_patterns, trace_data))
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    exit_code = _run_cli(
        monkeypatch,
        [
            "oracletrace",
            str(target),
            "--compare",
            str(compare_file),
            "--only-regressions",
        ],
    )

    captured = capsys.readouterr()
    assert f"{trace_data.functions[0].name}\n" in captured.out
    assert f"    total_time: {baseline_trace_data.functions[0].total_time:.4f}s → {trace_data.functions[0].total_time:.4f}s" in captured.out
    assert f"(+{33.33:.2f}%)\n" in captured.out
    assert f"{trace_data.functions[1].name}\n" not in captured.out

def test_main_prints_version_exits_0(monkeypatch, trace_data, capsys):
    module_name = "oracletrace"
    with pytest.raises(SystemExit):
        exit_code = _run_cli(monkeypatch,["oracletrace","--version",])

        captured = capsys.readouterr()
        assert exit_code == 0
        assert f"{module_name} {importlib.metadata.version(module_name)}" in captured.out


def test_main_repeat_runs_trace_multiple_times(monkeypatch, tmp_path, trace_data):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    tracer_instances = []

    def tracer_factory(root, ignore_patterns):
        fake = FakeTracer(root, ignore_patterns, trace_data)
        tracer_instances.append(fake)
        return fake

    run_count = 0

    def fake_run_path(*args, **kwargs):
        nonlocal run_count
        run_count += 1

    monkeypatch.setattr(cli, "Tracer", tracer_factory)
    monkeypatch.setattr(cli.runpy, "run_path", fake_run_path)

    exit_code = _run_cli(
        monkeypatch,
        [
            "oracletrace",
            str(target),
            "--repeat",
            "3",
        ],
    )

    assert exit_code == 0

    assert run_count == 3

    assert len(tracer_instances) == 3
    assert all(t.started for t in tracer_instances)
    assert all(t.stopped for t in tracer_instances)
    
def test_main_repeat_aggregates_function_times(monkeypatch, tmp_path):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    trace_data = TracerData(
        metadata=TracerMetadata(
            total_execution_time=1.0,
            total_functions=1,
            root_path=str(REPO_ROOT),
        ),
        functions=[
            FunctionData(
                name="foo",
                total_time=2.0,
                call_count=1,
                avg_time=2.0,
                callees=set(),
            )
        ],
    )

    def tracer_factory(root, ignore_patterns):
        return FakeTracer(root, ignore_patterns, trace_data)

    monkeypatch.setattr(cli, "Tracer", tracer_factory)
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    output_json = tmp_path / "trace.json"

    exit_code = _run_cli(
        monkeypatch,
        [
            "oracletrace",
            str(target),
            "--repeat",
            "3",
            "--json",
            str(output_json),
        ],
    )

    assert exit_code == 0

    exported = TracerData.from_dict(
        json.loads(output_json.read_text())
    )

    foo = exported.functions[0]

    assert foo.total_time == 2.0
    assert foo.call_count == 1
    
def test_main_repeat_does_not_call_show_results(monkeypatch, tmp_path, trace_data):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    fake_tracer_holder = {}

    def tracer_factory(root, ignore_patterns):
        fake = FakeTracer(root, ignore_patterns, trace_data)
        fake_tracer_holder["instance"] = fake
        return fake

    monkeypatch.setattr(cli, "Tracer", tracer_factory)
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    exit_code = _run_cli(
        monkeypatch,
        [
            "oracletrace",
            str(target),
            "--repeat",
            "2",
        ],
    )

    assert exit_code == 0

    fake_tracer = fake_tracer_holder["instance"]

    assert fake_tracer.show_results_calls == []
    
def test_main_repeat_one_behaves_like_default(monkeypatch, tmp_path, trace_data):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")

    fake_tracer_holder = {}

    def tracer_factory(root, ignore_patterns):
        fake = FakeTracer(root, ignore_patterns, trace_data)
        fake_tracer_holder["instance"] = fake
        return fake

    monkeypatch.setattr(cli, "Tracer", tracer_factory)
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    exit_code = _run_cli(
        monkeypatch,
        [
            "oracletrace",
            str(target),
            "--repeat",
            "1",
        ],
    )

    assert exit_code == 0

    fake_tracer = fake_tracer_holder["instance"]
    assert fake_tracer.show_results_calls == [None]    

def test_run_missing_command(monkeypatch, capsys):
    exit_code = _run_cli(monkeypatch, ["oracletrace", "run"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "no command specified" in captured.err


def test_run_unsupported_command(monkeypatch, capsys):
    # non-Python binaries can't be traced in-process and are rejected
    exit_code = _run_cli(monkeypatch, ["oracletrace", "run", "--", "mycmd"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "cannot trace 'mycmd'" in captured.err


def test_run_pytest_basic(monkeypatch, empty_trace_data):
    fake_tracer_holder: dict = {}
    def tracer_factory(root, ignore_patterns):
        fake = FakeTracer(root, ignore_patterns, empty_trace_data)
        fake_tracer_holder["instance"] = fake
        return fake
    monkeypatch.setattr(cli, "Tracer", tracer_factory)

    pytest_calls: list = []
    def fake_pytest_main(args=None):
        pytest_calls.append(args)
        return 0
    monkeypatch.setattr(pytest, "main", fake_pytest_main)

    exit_code = _run_cli(monkeypatch, ["oracletrace", "run", "--", "pytest"])

    fake_tracer = fake_tracer_holder["instance"]
    assert exit_code == 0
    assert fake_tracer.started is True
    assert fake_tracer.stopped is True
    assert pytest_calls == [[]]


def test_run_pytest_passes_args(monkeypatch, empty_trace_data):
    fake_tracer_holder: dict = {}
    def tracer_factory(root, ignore_patterns):
        fake = FakeTracer(root, ignore_patterns, empty_trace_data)
        fake_tracer_holder["instance"] = fake
        return fake
    monkeypatch.setattr(cli, "Tracer", tracer_factory)

    pytest_calls: list = []
    def fake_pytest_main(args=None):
        pytest_calls.append(args)
        return 0
    monkeypatch.setattr(pytest, "main", fake_pytest_main)

    exit_code = _run_cli(
        monkeypatch,
        ["oracletrace", "run", "--", "pytest", "-x", "-v", "tests/"],
    )

    assert exit_code == 0
    assert pytest_calls == [["-x", "-v", "tests/"]]


def test_run_pytest_propagates_pytest_exit_code(monkeypatch, empty_trace_data):
    fake_tracer_holder: dict = {}
    def tracer_factory(root, ignore_patterns):
        fake = FakeTracer(root, ignore_patterns, empty_trace_data)
        fake_tracer_holder["instance"] = fake
        return fake
    monkeypatch.setattr(cli, "Tracer", tracer_factory)

    def fake_pytest_main(args=None):
        return 1
    monkeypatch.setattr(pytest, "main", fake_pytest_main)

    exit_code = _run_cli(monkeypatch, ["oracletrace", "run", "--", "pytest"])

    assert exit_code == 1


def test_baseline_save_traces_script_and_writes_json(monkeypatch, tmp_path, trace_data, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")
    output = tmp_path / "baseline.json"

    fake_tracer_holder = {}

    def tracer_factory(root, ignore_patterns):
        fake = FakeTracer(root, ignore_patterns, trace_data)
        fake_tracer_holder["instance"] = fake
        return fake

    monkeypatch.setattr(cli, "Tracer", tracer_factory)
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    exit_code = _run_cli(
        monkeypatch,
        ["oracletrace", "baseline", "save", str(target), str(output)],
    )

    captured = capsys.readouterr()
    fake_tracer = fake_tracer_holder["instance"]

    assert exit_code == 0
    assert "Baseline saved:" in captured.out
    assert fake_tracer.started is True
    assert fake_tracer.stopped is True
    assert fake_tracer.show_results_calls == [None]
    assert TracerData.from_dict(json.loads(output.read_text(encoding="utf-8"))) == trace_data


def test_baseline_save_respects_repeat(monkeypatch, tmp_path, trace_data):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")
    output = tmp_path / "baseline.json"
    tracer_instances = []

    def tracer_factory(root, ignore_patterns):
        fake = FakeTracer(root, ignore_patterns, trace_data)
        tracer_instances.append(fake)
        return fake

    monkeypatch.setattr(cli, "Tracer", tracer_factory)
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    exit_code = _run_cli(
        monkeypatch,
        ["oracletrace", "baseline", "save", str(target), str(output), "--repeat", "3"],
    )

    assert exit_code == 0
    assert len(tracer_instances) == 3
    assert output.exists()


def test_baseline_compare_returns_0_without_regression(monkeypatch, tmp_path, trace_data):
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    baseline.write_text(json.dumps(asdict(trace_data), default=set_default), encoding="utf-8")
    current.write_text(json.dumps(asdict(trace_data), default=set_default), encoding="utf-8")

    compare_calls = []
    display_calls = []

    def fake_compare_traces(old_data, new_data, threshold):
        compare_calls.append((old_data, new_data, threshold))
        return ComparisonData(
            deltas=[], regressions=[], improvements=[],
            new_functions=[], removed_functions=[],
            threshold=threshold, has_regression=False,
        )

    monkeypatch.setattr(cli, "compare_traces", fake_compare_traces)
    monkeypatch.setattr(
        cli, "print_comparison",
        lambda comparison, only_regressions=False: display_calls.append(only_regressions),
    )

    exit_code = _run_cli(
        monkeypatch,
        [
            "oracletrace",
            "baseline",
            "compare",
            str(baseline),
            str(current),
            "--threshold",
            "12.5",
            "--only-regressions",
        ],
    )

    assert exit_code == 0
    assert compare_calls[0][2] == 12.5
    assert display_calls[0] is True


def test_baseline_compare_fails_with_exit_2_on_regression(monkeypatch, tmp_path, trace_data, capsys):
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    baseline.write_text(json.dumps(asdict(trace_data), default=set_default), encoding="utf-8")
    current.write_text(json.dumps(asdict(trace_data), default=set_default), encoding="utf-8")

    monkeypatch.setattr(
        cli,
        "compare_traces",
        lambda old_data, new_data, threshold: ComparisonData(
            deltas=[], regressions=[], improvements=[],
            new_functions=[], removed_functions=[],
            threshold=threshold, has_regression=True,
        ),
    )

    exit_code = _run_cli(
        monkeypatch,
        [
            "oracletrace",
            "baseline",
            "compare",
            str(baseline),
            str(current),
            "--fail-on-regression",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Build failed: performance regression above 5.00% detected." in captured.err


def test_baseline_compare_returns_1_when_files_are_missing(monkeypatch, tmp_path, capsys):
    exit_code = _run_cli(
        monkeypatch,
        [
            "oracletrace",
            "baseline",
            "compare",
            str(tmp_path / "missing-baseline.json"),
            str(tmp_path / "missing-current.json"),
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Baseline file not found:" in captured.err

