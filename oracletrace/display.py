"""All rich terminal output for comparisons lives here. compare.py returns
data; this module renders it — kept separate so new reporters (Markdown,
HTML, ...) can consume ComparisonData without re-implementing the logic.
"""

from rich import print

from .compare import (
    ComparisonData,
    NEW,
    NO_BASELINE,
    NO_SIGNAL,
    REGRESSION,
    REMOVED,
)
from .tracer import _safe_char

_ARROW = _safe_char("→", "->")


def print_comparison(comparison: ComparisonData, only_regressions: bool = False) -> None:
    print("\n[bold cyan]Comparison Results:[/]\n")

    for delta in comparison.deltas:
        if delta.status == NEW:
            print(f"[green]+ {delta.name} (new function)[/]")
            continue

        if delta.status == REMOVED:
            print(f"[red]- {delta.name} (removed)[/]")
            continue

        if delta.status == NO_SIGNAL:
            print(f"{delta.name} [yellow](no signal)[/]")
            continue

        if delta.status == NO_BASELINE:
            print(f"{delta.name} [yellow](no baseline)[/]")
            continue

        assert delta.percent is not None
        if only_regressions and delta.percent <= comparison.threshold:
            continue

        color = (
            "red" if delta.status == REGRESSION
            else "green" if delta.percent < -comparison.threshold
            else "yellow"
        )
        print(
            f"{delta.name}\n"
            f"    total_time: {delta.old_time:.4f}s {_ARROW} {delta.new_time:.4f}s "
            f"[{color}]({delta.percent:+.2f}%)[/]\n"
        )
