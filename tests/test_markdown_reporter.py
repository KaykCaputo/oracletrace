import pytest
from oracletrace.tracer import TracerData, TracerMetadata, FunctionData
from oracletrace.compare import compare_traces
from oracletrace.reporters import render_markdown, generate_markdown_report


@pytest.fixture
def trace_data() -> TracerData:
    return TracerData(
        metadata=TracerMetadata(
            root_path="/proj",
            total_functions=2,
            total_execution_time=2.5,
        ),
        functions=[
            FunctionData(name="app.py:main", total_time=2.0, call_count=1, avg_time=2.0, callees=set()),
            FunctionData(name="app.py:helper", total_time=0.5, call_count=4, avg_time=0.125, callees=set()),
        ],
    )


@pytest.fixture
def baseline_data() -> TracerData:
    return TracerData(
        metadata=TracerMetadata(root_path="/proj", total_functions=2, total_execution_time=2.0),
        functions=[
            FunctionData(name="app.py:main", total_time=1.0, call_count=1, avg_time=1.0, callees=set()),
            FunctionData(name="app.py:helper", total_time=0.5, call_count=4, avg_time=0.125, callees=set()),
        ],
    )


class TestRenderMarkdown:
    def test_header_and_summary(self, trace_data):
        md = render_markdown(trace_data)
        assert md.startswith("## ⚡ OracleTrace Performance Report")
        assert "**Total time:** 2.5000s" in md
        assert "**Functions:** 2" in md

    def test_top_functions_table_sorted_desc(self, trace_data):
        md = render_markdown(trace_data)
        assert "| Function | Total Time (s) | Calls | Avg (ms) |" in md
        main_pos = md.index("app.py:main")
        helper_pos = md.index("app.py:helper")
        assert main_pos < helper_pos  # hottest first

    def test_top_limit(self, trace_data):
        md = render_markdown(trace_data, top=1)
        assert "app.py:main" in md
        # helper appears only in the top table, which is truncated to 1
        assert md.count("app.py:helper") == 0

    def test_no_comparison_section_without_baseline(self, trace_data):
        md = render_markdown(trace_data)
        assert "Comparison vs. baseline" not in md

    def test_pipe_in_name_is_escaped(self):
        data = TracerData(
            metadata=TracerMetadata(root_path="/p", total_functions=1, total_execution_time=1.0),
            functions=[FunctionData(name="a.py:f|g", total_time=1.0, call_count=1, avg_time=1.0, callees=set())],
        )
        md = render_markdown(data)
        assert "f\\|g" in md
        assert "| a.py:f|g |" not in md  # raw pipe would break the table


class TestComparisonSection:
    def test_regression_rendered_with_icon(self, baseline_data, trace_data):
        comparison = compare_traces(baseline_data, trace_data, threshold=5.0)
        md = render_markdown(trace_data, comparison=comparison)
        assert "### Comparison vs. baseline" in md
        assert "🔴" in md
        assert "app.py:main" in md
        assert "+100.0%" in md
        assert "🚨 **1 regression(s)** above 5.0% threshold" in md

    def test_no_regression_shows_green_banner(self, baseline_data):
        comparison = compare_traces(baseline_data, baseline_data, threshold=5.0)
        md = render_markdown(baseline_data, comparison=comparison)
        assert "✅ No regressions above 5.0% threshold" in md

    def test_new_and_removed_functions_listed(self):
        old = TracerData(
            metadata=TracerMetadata(root_path="/p", total_functions=1, total_execution_time=1.0),
            functions=[FunctionData(name="a.py:gone", total_time=1.0, call_count=1, avg_time=1.0, callees=set())],
        )
        new = TracerData(
            metadata=TracerMetadata(root_path="/p", total_functions=1, total_execution_time=1.0),
            functions=[FunctionData(name="a.py:fresh", total_time=1.0, call_count=1, avg_time=1.0, callees=set())],
        )
        comparison = compare_traces(old, new, threshold=5.0)
        md = render_markdown(new, comparison=comparison)
        assert "**New:** `a.py:fresh`" in md
        assert "**Removed:** `a.py:gone`" in md


class TestGenerateMarkdownReport:
    def test_writes_file(self, trace_data, tmp_path):
        out = tmp_path / "report.md"
        generate_markdown_report(trace_data, str(out))
        content = out.read_text(encoding="utf-8")
        assert content.startswith("## ⚡ OracleTrace Performance Report")
        assert "app.py:main" in content

    def test_self_contained_no_external_urls_except_footer(self, trace_data, tmp_path):
        out = tmp_path / "report.md"
        generate_markdown_report(trace_data, str(out))
        content = out.read_text(encoding="utf-8")
        # the only link is the OracleTrace footer
        assert content.count("https://") == 1
        assert "github.com/KaykCaputo/oracletrace" in content
