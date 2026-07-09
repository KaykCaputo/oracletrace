import pytest
from oracletrace.tracer import TracerData, TracerMetadata, FunctionData
from oracletrace.reporters.html import generate_html_report


@pytest.fixture
def sample_trace_data():
    return TracerData(
        metadata=TracerMetadata(
            root_path="/test/project",
            total_functions=3,
            total_execution_time=1.5
        ),
        functions=[
            FunctionData(
                name="main.py:main",
                total_time=1.0,
                call_count=1,
                avg_time=1.0,
                callees=["main.py:helper"]
            ),
            FunctionData(
                name="main.py:helper",
                total_time=0.4,
                call_count=3,
                avg_time=0.133,
                callees=["main.py:compute"]
            ),
            FunctionData(
                name="main.py:compute",
                total_time=0.1,
                call_count=10,
                avg_time=0.01,
                callees=[]
            )
        ]
    )


def test_generate_html_report(sample_trace_data, tmp_path):
    output_path = str(tmp_path / "report.html")
    generate_html_report(sample_trace_data, output_path)

    content = tmp_path.joinpath("report.html").read_text(encoding="utf-8")

    assert "<!DOCTYPE html>" in content
    assert "OracleTrace Report" in content
    assert "/test/project" in content
    assert "1.5" in content
    assert "3" in content


def test_html_report_contains_table_columns(sample_trace_data, tmp_path):
    output_path = str(tmp_path / "report.html")
    generate_html_report(sample_trace_data, output_path)

    content = tmp_path.joinpath("report.html").read_text(encoding="utf-8")

    assert "Function</th>" in content
    assert "Total Time (s)</th>" in content
    assert "Calls</th>" in content
    assert "Avg Time (ms)</th>" in content
    assert "Callees</th>" in content


def test_html_report_is_standalone(sample_trace_data, tmp_path):
    output_path = str(tmp_path / "report.html")
    generate_html_report(sample_trace_data, output_path)

    content = tmp_path.joinpath("report.html").read_text(encoding="utf-8")

    assert "https://" not in content and "http://" not in content


def test_html_report_contains_function_names(sample_trace_data, tmp_path):
    output_path = str(tmp_path / "report.html")
    generate_html_report(sample_trace_data, output_path)

    content = tmp_path.joinpath("report.html").read_text(encoding="utf-8")

    assert "main.py:main" in content
    assert "main.py:helper" in content
    assert "main.py:compute" in content


def test_html_report_callees_rendered(sample_trace_data, tmp_path):
    output_path = str(tmp_path / "report.html")
    generate_html_report(sample_trace_data, output_path)

    content = tmp_path.joinpath("report.html").read_text(encoding="utf-8")

    assert "main.py:helper" in content
    assert "main.py:compute" in content
    assert "callees" in content.lower() or "callee" in content.lower()


def test_html_report_uses_template_delimiter(sample_trace_data, tmp_path):
    output_path = str(tmp_path / "report.html")
    generate_html_report(sample_trace_data, output_path)

    content = tmp_path.joinpath("report.html").read_text(encoding="utf-8")

    # Placeholders should be replaced - @ should not appear as a placeholder
    # (it would only remain if substitution failed)
    assert "@root_path" not in content
    assert "@total_time" not in content
    assert "@functions_json" not in content


def test_html_report_empty_functions(sample_trace_data, tmp_path):
    empty_data = TracerData(
        metadata=TracerMetadata(
            root_path="/empty",
            total_functions=0,
            total_execution_time=0.0
        ),
        functions=[]
    )
    output_path = str(tmp_path / "report.html")
    generate_html_report(empty_data, output_path)

    content = tmp_path.joinpath("report.html").read_text(encoding="utf-8")

    assert "[]" in content
    assert "/empty" in content


def test_script_breakout_in_function_name_is_neutralized(tmp_path):
    data = TracerData(
        metadata=TracerMetadata(
            root_path="/test/project", total_functions=1, total_execution_time=1.0
        ),
        functions=[
            FunctionData(
                name='evil.py:</script><script>alert(1)</script>',
                total_time=1.0,
                call_count=1,
                avg_time=1.0,
                callees=['evil.py:</script><img src=x onerror=alert(2)>'],
            )
        ],
    )
    output = tmp_path / "report.html"
    generate_html_report(data, str(output))
    html = output.read_text(encoding="utf-8")

    # a literal </script> inside the embedded JSON would terminate the
    # report's own script block at parse time
    assert "<script>alert(1)</script>" not in html
    assert "<img src=x onerror" not in html
    assert "\u003c/script" in html  # payload survives, JSON-escaped


def test_root_path_is_html_escaped(tmp_path):
    data = TracerData(
        metadata=TracerMetadata(
            root_path='/proj/<img src=x onerror=alert(3)>',
            total_functions=0,
            total_execution_time=0.0,
        ),
        functions=[],
    )
    output = tmp_path / "report.html"
    generate_html_report(data, str(output))
    html = output.read_text(encoding="utf-8")
    assert "<img src=x onerror=alert(3)>" not in html
    assert "&lt;img" in html
