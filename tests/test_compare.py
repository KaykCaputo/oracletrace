import pytest
import sys
from oracletrace.tracer import TracerData, TracerMetadata, FunctionData
from oracletrace.compare import compare_traces, ComparisonData, RegressionData

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


def test_compare_regression(baseline_trace_data, trace_data_regression):
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

def test_compare_improvement(baseline_trace_data, trace_data_improvement): 
    result = compare_traces(old_data=baseline_trace_data, new_data=trace_data_improvement)
    assert not result.has_regression

def test_compare_unchanged(baseline_trace_data, trace_data_unchanged): 
    result = compare_traces(old_data=baseline_trace_data, new_data=trace_data_unchanged)
    assert not result.has_regression

def test_compare_new_function(baseline_trace_data, trace_data_new_function, capsys): 
    compare_traces(old_data=baseline_trace_data, new_data=trace_data_new_function)
    stdoutlines = capsys.readouterr().out.split("\n")
    assert f"+ {trace_data_new_function.functions[2].name} (new function)" in stdoutlines

def test_compare_removed_function(baseline_trace_data, trace_data_function_removed, capsys): 
    compare_traces(old_data=baseline_trace_data, new_data=trace_data_function_removed)
    stdoutlines = capsys.readouterr().out.split("\n")
    assert f"- {baseline_trace_data.functions[1].name} (removed)" in stdoutlines

def test_compare_old_time_0_no_baseline(baseline_trace_data_old_time_null, trace_data_unchanged, capsys): 
    compare_traces(old_data=baseline_trace_data_old_time_null, new_data=trace_data_unchanged)
    stdoutlines = capsys.readouterr().out.split("\n")
    assert f"{baseline_trace_data_old_time_null.functions[0].name} (no baseline)" in stdoutlines

def test_compare_old_time_0_no_signal(baseline_trace_data_old_time_null, trace_data_no_signal, capsys): 
    compare_traces(old_data=baseline_trace_data_old_time_null, new_data=trace_data_no_signal)
    stdoutlines = capsys.readouterr().out.split("\n")
    assert f"{baseline_trace_data_old_time_null.functions[0].name} (no signal)" in stdoutlines

def test_compare_only_regressions(baseline_trace_data, trace_data_regression, capsys):
    result = compare_traces(old_data=baseline_trace_data, new_data=trace_data_regression, show_only_regressions=True)
    stdout = capsys.readouterr().out
    assert f"{baseline_trace_data.functions[1].name}\n" in stdout
    assert f"{baseline_trace_data.functions[0].name}\n" not in stdout

def test_compare_only_regressions_1_percent_regression(baseline_trace_data, trace_data_1_percent_regression,capsys):
    result = compare_traces(old_data=baseline_trace_data, new_data=trace_data_1_percent_regression, show_only_regressions=True)
    stdout = capsys.readouterr().out
    assert f"{baseline_trace_data.functions[1].name}\n" not in stdout
    assert f"{baseline_trace_data.functions[0].name}\n" not in stdout