from .tracer import TracerData, FunctionData
from rich import print
from typing import Any, Dict, List, Set, Optional
from dataclasses import dataclass

@dataclass
class RegressionData:
    name: str
    old_time: float
    new_time: float
    percent: float

@dataclass
class ComparisonData:
    regressions: List[RegressionData]
    has_regression: bool

def compare_traces(
    old_data: TracerData,
    new_data: TracerData,
    threshold: float = 5.0,
    show_only_regressions: bool = False
) -> ComparisonData:
    old_funcs: Dict[str, FunctionData] = {f.name: f for f in old_data.functions}
    new_funcs: Dict[str, FunctionData] = {f.name: f for f in new_data.functions}

    regressions: List[RegressionData] = []

    print("\n[bold cyan]Comparison Results:[/]\n")

    all_functions: Set[str] = set(old_funcs) | set(new_funcs)

    for name in sorted(all_functions):
        old: Optional[FunctionData] = old_funcs.get(name)
        new: Optional[FunctionData] = new_funcs.get(name)

        if not old:
            print(f"[green]+ {name} (new function)[/]")
            continue

        if not new:
            print(f"[red]- {name} (removed)[/]")
            continue

        old_time: float = old.total_time
        new_time: float = new.total_time

        if old_time == 0:
            continue

        diff: float = new_time - old_time
        percent: float = (diff / old_time) * 100

        color: str = "red" if percent > threshold else "green" if percent < -threshold else "yellow"

        print(
            f"{name}\n"
            f"    total_time: {old_time:.4f}s → {new_time:.4f}s "
            f"[{color}]({percent:+.2f}%)[/]\n"
        ) if not show_only_regressions or diff > 0.0 else ...
        
        
        if percent > threshold:
            regressions.append(
                RegressionData(
                        name = name,
                        new_time = new_time,
                        old_time = old_time,
                        percent = percent
                    )
            )

    return ComparisonData(
        regressions = regressions,
        has_regression = len(regressions) > 0
    )
