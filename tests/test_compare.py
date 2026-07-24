import pytest
import sys
from oracletrace.tracer import TracerData, TracerMetadata, FunctionData
from oracletrace.compare import (
    compare_traces,
    ComparisonData,
    FunctionDelta,
    RegressionData,
    NEW,
    REMOVED,
    NO_SIGNAL,
    NO_BASELINE,
    REGRESSION,
    IMPROVEMENT,
    STABLE,
)

@pytest.fixture()
def baseline_trace_data() -> TracerData:
    return TracerData(
        metadata=TracerMetadata(
            root_path="",
            total_functions=2,
            total_execution_time=3.0
        ),
        functions=[
            FunctionData(
                name="foo",
                total_time=1.0,
                call_count=2,
                avg_time=0.5,
                callees=[]
            ),
            FunctionData(
                name="bar",
                total_time=2.0,
                call_count=3,
                avg_time=0.67,
                callees=[]
            )
        ]
    )

@pytest.fixture()
def baseline_trace_data_old_time_null() -> TracerData:
    return TracerData(
        metadata=TracerMetadata(
            root_path="",
            total_functions=2,
            total_execution_time=2.0
        ),
        functions=[
            FunctionData(
                name="foo",
                total_time=0.0,
                call_count=1,
                avg_time=0.0,
                callees=[]
            ),
            FunctionData(
                name="bar",
                total_time=2.0,
                call_count=3,
                avg_time=0.67,
                callees=[]
            )
        ]
    )


@pytest.fixture
def trace_data_regression() -> TracerData:
    return TracerData(
        metadata=TracerMetadata(
            root_path="",
            total_functions=2,
            total_execution_time=3.4
        ),
        functions=[
            FunctionData(
                name="foo",
                total_time=1.0,
                call_count=2,
                avg_time=0.5,
                callees=[]
            ),
            FunctionData(
                name="bar",
                total_time=2.4,
                call_count=3,
                avg_time=0.8,
                callees=[]
            )
        ]

    )

@pytest.fixture
def trace_data_improvement() -> TracerData:
    return TracerData(
        metadata=TracerMetadata(
            root_path="",
            total_functions=2,
            total_execution_time=2.5
        ),
        functions=[
            FunctionData(
                name="foo",
                total_time=1.0,
                call_count=2,
                avg_time=0.5,
                callees=[]
            ),
            FunctionData(
                name="bar",
                total_time=1.5,
                call_count=3,
                avg_time=0.5,
                callees=[]
            )
        ]

    )

@pytest.fixture
def trace_data_unchanged() -> TracerData:
    # no significant change
    return TracerData(
        metadata=TracerMetadata(
            root_path="",
            total_functions=1,
            total_execution_time=3.01
        ),
        functions=[
            FunctionData(
                name="foo",
                total_time=1.01,
                call_count=2,
                avg_time=0.505,
                callees=[]
            ),
            FunctionData(
                name="bar",
                total_time=2.0,
                call_count=3,
                avg_time=0.67,
                callees=[]
            )
        ]
    )

@pytest.fixture
def trace_data_function_removed() -> TracerData:
    return TracerData(
        metadata=TracerMetadata(
            root_path="",
            total_functions=1,
            total_execution_time=1.0
        ),
        functions=[
            FunctionData(
                name="foo",
                total_time=1.0,
                call_count=2,
                avg_time=0.5,
                callees=[]
            )
        ]
    )

@pytest.fixture
def trace_data_new_function() -> TracerData:
    return TracerData(
        metadata=TracerMetadata(
            root_path="",
            total_functions=3,
            total_execution_time=4.2
        ),
        functions=[
            FunctionData(
                name="foo",
                total_time=1.0,
                call_count=2,
                avg_time=0.5,
                callees=[]
            ),
            FunctionData(
                name="bar",
                total_time=2.0,
                call_count=3,
                avg_time=0.67,
                callees=[]
            ),
            FunctionData(
                name="xyz",
                total_time=1.2,
                call_count=2,
                avg_time=0.6,
                callees=[]
            )
        ]
    )

@pytest.fixture()
def trace_data_no_signal() -> TracerData:
    return TracerData(
        metadata=TracerMetadata(
            root_path="",
            total_functions=2,
            total_execution_time=2.0
        ),
        functions=[
            FunctionData(
                name="foo",
                total_time=0.0,
                call_count=1,
                avg_time=0.0,
                callees=[]
            ),
            FunctionData(
                name="bar",
                total_time=2.0,
                call_count=3,
                avg_time=0.67,
                callees=[]
            )
        ]
    )

@pytest.fixture()
def trace_data_1_percent_regression() -> TracerData:
    return TracerData(
        metadata=TracerMetadata(
            root_path="",
            total_functions=2,
            total_execution_time=2.0
        ),
        functions=[
            FunctionData(
                name="foo",
                total_time=0.0,
                call_count=1,
                avg_time=0.0,
                callees=[]
            ),
            FunctionData(
                name="bar",
                total_time=2.02,
                call_count=3,
                avg_time=0.67,
                callees=[]
            )
        ]
    )


def _delta(result: ComparisonData, name: str) -> FunctionDelta:
    return next(d for d in result.deltas if d.name == name)


class TestCompareTracesIsPure:
    """compare_traces() must be a pure function: given the same inputs it
    returns the same ComparisonData, with no printing or other side effects."""

    def test_no_output_produced(self, baseline_trace_data, trace_data_regression, capsys):
        compare_traces(old_data=baseline_trace_data, new_data=trace_data_regression)
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""


class TestRegressionsAndImprovements:
    def test_compare_regression(self, baseline_trace_data, trace_data_regression):
        result = compare_traces(old_data=baseline_trace_data, new_data=trace_data_regression)

        old_time = baseline_trace_data.functions[1].total_time
        new_time = trace_data_regression.functions[1].total_time
        percent = (new_time - old_time) / old_time * 100
        assert len(result.regressions) == 1
        assert result.regressions[0] == RegressionData(
            name=trace_data_regression.functions[1].name,
            old_time=old_time,
            new_time=new_time,
            percent=percent
        )
        default_regression_threshold = compare_traces.__defaults__[0]
        assert result.regressions[0].percent > default_regression_threshold
        assert _delta(result, "bar").status == REGRESSION

    def test_compare_improvement(self, baseline_trace_data, trace_data_improvement):
        result = compare_traces(old_data=baseline_trace_data, new_data=trace_data_improvement)
        assert not result.has_regression
        assert len(result.improvements) == 1
        assert _delta(result, "bar").status == IMPROVEMENT

    def test_compare_unchanged(self, baseline_trace_data, trace_data_unchanged):
        result = compare_traces(old_data=baseline_trace_data, new_data=trace_data_unchanged)
        assert not result.has_regression
        assert _delta(result, "foo").status == STABLE


class TestNewAndRemoved:
    def test_compare_new_function(self, baseline_trace_data, trace_data_new_function):
        result = compare_traces(old_data=baseline_trace_data, new_data=trace_data_new_function)
        assert trace_data_new_function.functions[2].name in result.new_functions
        assert _delta(result, trace_data_new_function.functions[2].name).status == NEW

    def test_compare_removed_function(self, baseline_trace_data, trace_data_function_removed):
        result = compare_traces(old_data=baseline_trace_data, new_data=trace_data_function_removed)
        assert baseline_trace_data.functions[1].name in result.removed_functions
        assert _delta(result, baseline_trace_data.functions[1].name).status == REMOVED


class TestZeroBaseline:
    def test_compare_old_time_0_no_baseline(self, baseline_trace_data_old_time_null, trace_data_unchanged):
        result = compare_traces(old_data=baseline_trace_data_old_time_null, new_data=trace_data_unchanged)
        assert _delta(result, baseline_trace_data_old_time_null.functions[0].name).status == NO_BASELINE

    def test_compare_old_time_0_no_signal(self, baseline_trace_data_old_time_null, trace_data_no_signal):
        result = compare_traces(old_data=baseline_trace_data_old_time_null, new_data=trace_data_no_signal)
        assert _delta(result, baseline_trace_data_old_time_null.functions[0].name).status == NO_SIGNAL


class TestDeltasCoverEveryFunction:
    def test_deltas_include_all_functions_regardless_of_status(
        self, baseline_trace_data, trace_data_regression
    ):
        result = compare_traces(old_data=baseline_trace_data, new_data=trace_data_regression)
        assert {d.name for d in result.deltas} == {"foo", "bar"}
