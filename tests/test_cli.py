import json
import importlib
import sys
from pathlib import Path
from oracletrace.tracer import TracerData, FunctionData, TracerMetadata
from oracletrace.compare import ComparisonData
from dataclasses import asdict
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.modules.pop("oracletrace.cli", None)
sys.modules.pop("oracletrace", None)
cli = importlib.import_module("oracletrace.cli")
assert str(REPO_ROOT / "oracletrace") in str(Path(cli.__file__).resolve())


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
                name = "foo",
                total_time = 3.033,
                call_count = 3,
                avg_time = 1.011,
                callees=[]
            ),
            FunctionData(
                name = "bar",
                total_time = 2.0,
                call_count = 2,
                avg_time = 1.0,
                callees=[]
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
                callees=[]
            ),
            FunctionData(
                name = "bar",
                total_time = 2.0,
                call_count = 2,
                avg_time = 1.0,
                callees=[]
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
    assert "Target not found: missing_script.py" in captured.out


def test_main_returns_1_when_ignore_regex_is_invalid(monkeypatch, tmp_path, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('ok')\n", encoding="utf-8")

    exit_code = _run_cli(monkeypatch, ["oracletrace", str(target), "--ignore", "["])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Regex error: [" in captured.out


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
    assert "foo,3.033,3,1.011" in csv_text
    assert "bar,2.0,2,1.0" in csv_text

    assert sys.path[0] == str(target.parent.resolve())


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
    assert "Compare file not found:" in captured.out


def test_main_fails_with_exit_2_on_regression(monkeypatch, tmp_path, empty_trace_data, capsys):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")
    compare_file = tmp_path / "baseline.json"
    compare_file.write_text(json.dumps(asdict(empty_trace_data)), encoding="utf-8")

    monkeypatch.setattr(cli, "Tracer", lambda root, ignore_patterns: FakeTracer(root, ignore_patterns, empty_trace_data))
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)

    compare_calls = []

    def fake_compare_traces(old_data, new_data, threshold, show_only_regressions):
        compare_calls.append((old_data, new_data, threshold, show_only_regressions))
        return ComparisonData(regressions=[], has_regression=True)

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
    assert "Build failed: performance regression above 7.50% detected." in captured.out
    assert compare_calls[0][2] == 7.5


def test_main_returns_0_when_no_regression(monkeypatch, tmp_path, trace_data):
    target = tmp_path / "target.py"
    target.write_text("print('hello')\n", encoding="utf-8")
    compare_file = tmp_path / "baseline.json"
    compare_file.write_text(json.dumps(asdict(trace_data)), encoding="utf-8")

    monkeypatch.setattr(cli, "Tracer", lambda root, ignore_patterns: FakeTracer(root, ignore_patterns, trace_data))
    monkeypatch.setattr(cli.runpy, "run_path", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        cli,
        "compare_traces",
        lambda old_data, new_data, threshold, show_only_regressions: ComparisonData(
            regressions=[],
            has_regression=False
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
    compare_file.write_text(json.dumps(asdict(baseline_trace_data)), encoding="utf-8")
    
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
    assert f"(+{102.2:.2f}%)\n" in captured.out
    assert f"{trace_data.functions[1].name}\n" not in captured.out
