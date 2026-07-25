"""Pure comparison logic. No printing, no side effects — returns structured
data that any reporter (terminal, Markdown, HTML, ...) can render.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from .tracer import TracerData, FunctionData

# Delta status values
REGRESSION = "regression"
IMPROVEMENT = "improvement"
STABLE = "stable"
NEW = "new"
REMOVED = "removed"
NO_SIGNAL = "no_signal"      # both runs recorded zero time
NO_BASELINE = "no_baseline"  # baseline recorded zero time


@dataclass
class FunctionDelta:
    name: str
    status: str
    old_time: Optional[float] = None
    new_time: Optional[float] = None
    percent: Optional[float] = None


@dataclass
class RegressionData:
    name: str
    old_time: float
    new_time: float
    percent: float


@dataclass
class ComparisonData:
    deltas: List[FunctionDelta]
    regressions: List[RegressionData]
    improvements: List[RegressionData]
    new_functions: List[str]
    removed_functions: List[str]
    threshold: float
    has_regression: bool


def compare_traces(
    old_data: TracerData,
    new_data: TracerData,
    threshold: float = 5.0,
) -> ComparisonData:
    old_funcs: Dict[str, FunctionData] = {f.name: f for f in old_data.functions}
    new_funcs: Dict[str, FunctionData] = {f.name: f for f in new_data.functions}

    deltas: List[FunctionDelta] = []
    regressions: List[RegressionData] = []
    improvements: List[RegressionData] = []
    new_functions: List[str] = []
    removed_functions: List[str] = []

    all_functions: Set[str] = set(old_funcs) | set(new_funcs)

    for name in sorted(all_functions):
        old: Optional[FunctionData] = old_funcs.get(name)
        new: Optional[FunctionData] = new_funcs.get(name)

        if not old:
            new_functions.append(name)
            deltas.append(FunctionDelta(
                name=name, status=NEW,
                new_time=new.total_time if new else None,
            ))
            continue

        if not new:
            removed_functions.append(name)
            deltas.append(FunctionDelta(
                name=name, status=REMOVED, old_time=old.total_time,
            ))
            continue

        old_time: float = old.total_time
        new_time: float = new.total_time

        if old_time == 0:
            status = NO_SIGNAL if new_time == 0 else NO_BASELINE
            deltas.append(FunctionDelta(
                name=name, status=status, old_time=old_time, new_time=new_time,
            ))
            continue

        percent: float = ((new_time - old_time) / old_time) * 100

        if percent > threshold:
            status = REGRESSION
            regressions.append(RegressionData(
                name=name, old_time=old_time, new_time=new_time, percent=percent,
            ))
        elif percent < -threshold:
            status = IMPROVEMENT
            improvements.append(RegressionData(
                name=name, old_time=old_time, new_time=new_time, percent=percent,
            ))
        else:
            status = STABLE

        deltas.append(FunctionDelta(
            name=name, status=status,
            old_time=old_time, new_time=new_time, percent=percent,
        ))

    return ComparisonData(
        deltas=deltas,
        regressions=regressions,
        improvements=improvements,
        new_functions=new_functions,
        removed_functions=removed_functions,
        threshold=threshold,
        has_regression=len(regressions) > 0,
    )
