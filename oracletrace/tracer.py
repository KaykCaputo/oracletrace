import os
import sys
import site
import time
import sysconfig
from re import Pattern
from pathlib import Path
from types import FrameType
from statistics import median
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional, Callable, DefaultDict, Any, Tuple, Dict, Self

from rich import print
from rich.tree import Tree
from rich.table import Table

@dataclass
class TracerMetadata:
    root_path: str
    total_functions: int
    total_execution_time: float

@dataclass
class FunctionData:
    name: str
    total_time: float
    call_count: int
    avg_time: float
    callees: set[str] = field(default_factory=set)

    def add(self, trace: Self) -> None:
        if trace.name != self.name:
            return

        self.callees.update(trace.callees)
        self.total_time += trace.total_time
        self.call_count += trace.call_count

        if self.call_count:
            self.avg_time = self.total_time / self.call_count

@dataclass
class TracerData:
    metadata: TracerMetadata
    functions: List[FunctionData]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TracerData":
        return cls(
            metadata=TracerMetadata(**data["metadata"]),
            functions=[
                FunctionData(
                    **{
                        **f,
                        "callees": set(f.get("callees", [])),
                    }
                )
                for f in data["functions"]
            ],
        )

@dataclass
class FunctionAggregate:
    name: str
    total_times: List[float] = field(default_factory=list)
    call_counts: List[int] = field(default_factory=list)
    callees: set[str] = field(default_factory=set)

    def add(self, data: FunctionData) -> None:
        self.total_times.append(data.total_time)
        self.call_counts.append(data.call_count)
        self.callees.update(data.callees)

    def to_function_data(self) -> FunctionData:
        total_time = median(self.total_times)
        call_count = int(median(self.call_counts))

        return FunctionData(
            name=self.name,
            total_time=total_time,
            call_count=call_count,
            avg_time=total_time / call_count if call_count else 0,
            callees=self.callees,
        )

class Tracer:
    def __init__(self, root_dir: str, ignore_patterns: Optional[List[Pattern]] = None) -> None:
        self._root_path: str = os.path.abspath(root_dir)
        self._call_stack: List[Tuple[int, str, float]] = []
        self._func_calls: DefaultDict[str, int] = defaultdict(int)
        self._func_time: DefaultDict[str, float] = defaultdict(float)
        self._call_map: DefaultDict[str, DefaultDict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._original_profile_func: Optional[Callable[[FrameType, str, Any], object]] = None
        self._enabled: bool = False
        self._start_time: float = 0.0          
        self._total_time: float = 0.0
        self._ignore_patterns: Optional[List[Pattern]] = ignore_patterns


    def start(self) -> None:
        # Start Tracer
        self._enabled = True
        self._start_time = time.perf_counter()          
        self._original_profile_func = sys.getprofile()
        sys.setprofile(self._trace)

    def stop(self) -> None:
        # Stops Tracer
        self._enabled = False
        self._total_time = time.perf_counter() - self._start_time  
        sys.setprofile(self._original_profile_func)

    def _is_ignored(self, filename: str) -> bool:
        # Return true if the filename should be ignored
        if not self._ignore_patterns:
            return False

        for pattern in self._ignore_patterns:
            if pattern.search(filename):
                return True

        return False

    def _is_user_code(self, filename: str) -> bool:
        # Normalize all paths to resolve symlinks
        filename = os.path.realpath(filename)
        root_path = os.path.realpath(self._root_path)

        # Check project root
        if os.path.commonpath([root_path, filename]) != root_path:
            return False

        # Exclude Python stdlib
        stdlib_path = os.path.realpath(sysconfig.get_path("stdlib"))
        if os.path.commonpath([stdlib_path, filename]) == stdlib_path:
            return False

        # Exclude all site-packages
        site_paths = site.getsitepackages() + [site.getusersitepackages()]
        normalized_site_paths = [os.path.realpath(p) for p in site_paths]
        for sp in normalized_site_paths:
            if os.path.commonpath([sp, filename]) == sp:
                return False

        # Exclude venv-like directories that may be inside the project root
        venv_markers = {"venv", ".venv", "env", ".env", "virtualenv"}
        path_relative_to_root = os.path.relpath(filename, root_path)
        path_parts = Path(path_relative_to_root).parts
        if any(part in venv_markers for part in path_parts):
            return False
        return True

    def _get_key(self, frame: FrameType) -> Optional[str]:
        co_filename: str = frame.f_code.co_filename
        # Ignore internal python frames (e.g. <string>)
        if co_filename.startswith("<"):
            return None
        filename: str = os.path.abspath(co_filename)
        # Check if the file belongs to the user's project
        if not self._is_user_code(filename):
            return None
        # Create a relative path key for readability
        rel_path: str = os.path.relpath(filename, self._root_path)
        qualname: str = getattr(frame.f_code, "co_qualname", frame.f_code.co_name)
        key: str = f"{rel_path}:{qualname}"

        # Check if the file should be ignored based on inputted ignoring pattern
        if self._is_ignored(key):
            return None

        return key

    def _trace(self, frame: FrameType, event: str, _: Any) -> None:
        try:
            if not self._enabled:
                return

            if event == "call":
                key: Optional[str] = self._get_key(frame)
                if not key:
                    return

                caller: str = self._call_stack[-1][1] if self._call_stack else "<module>"
                self._call_map[caller][key] += 1
                self._func_calls[key] += 1
                self._call_stack.append((id(frame), key, time.perf_counter()))

            elif event == "return":
                if not self._call_stack:
                    return

                # Optimization: check if the returning frame is at the top of the stack
                if id(frame) == self._call_stack[-1][0]:
                    _, key, start = self._call_stack.pop()
                    self._func_time[key] += time.perf_counter() - start
                else:
                    # Stack unwinding (handle exceptions or missed returns)
                    fid: int = id(frame)
                    found: bool = False
                    # Search for the frame in the stack from top to bottom
                    for i in range(len(self._call_stack) - 1, -1, -1):
                        if self._call_stack[i][0] == fid:
                            found = True
                            break

                    if found:
                        # Pop everything until we find the matching frame
                        while self._call_stack:
                            top_fid, key, start = self._call_stack.pop()
                            self._func_time[key] += time.perf_counter() - start
                            if top_fid == fid:
                                break
        except Exception as e:
            print(f"[bold red]Error in oracletrace tracer: {e}[/]", file=sys.stderr)

    def show_results(self, _top: Optional[int]) -> None:
        if not self._func_calls:
            print("[yellow]No calls traced.[/]")
            return

        # Summary table
        print("[bold green]Summary:[/]")
        print(f"[bold cyan]Total execution time: {self._total_time:.4f}s[/]")
        table: Table = Table(title="Top functions by Total Time")
        table.add_column("Function", justify="left", style="cyan", no_wrap=True)
        table.add_column("Total Time (s)", justify="right", style="magenta")
        table.add_column("Calls", justify="right", style="green")
        table.add_column("Avg. Time/Call (ms)", justify="right", style="yellow")

        # sort functions by time
        _sorted_by_time = sorted(
            self._func_time.items(), key=lambda item: item[1], reverse=True
        )

        for key, total_time in _sorted_by_time[:_top]:
            calls = self._func_calls[key]
            avg_time_ms = (total_time / calls) * 1000 if calls > 0 else 0
            table.add_row(key, f"{total_time:.4f}", str(calls), f"{avg_time_ms:.3f}")

        print(table)

        print("\n[bold green]Logic Flow:[/]")

        tree: Tree = Tree("[bold yellow]<module>[/]")

        # Recursively build the execution tree
        def add_nodes(parent_node: Tree, parent_key: str, current_path: set[str]) -> None:
            children: DefaultDict[str,int] = self._call_map.get(parent_key, defaultdict(int))
            # Sort children by total execution time
            sorted_children = sorted(
                children.items(),
                key=lambda x: self._func_time.get(x[0], 0),
                reverse=True,
            )

            for child_key, count in sorted_children:
                _total_time = self._func_time[child_key]
                # Detect recursion to prevent infinite loops in the tree
                if child_key in current_path:
                    parent_node.add(f"[red]↻ {child_key}[/] ({count}x)")
                    continue

                node_text = f"{child_key} [dim]({count}x, {_total_time:.4f}s)[/]"
                child_node = parent_node.add(node_text)
                add_nodes(child_node, child_key, current_path | {child_key})

        add_nodes(tree, "<module>", {"<module>"})
        print(tree)

    def get_trace_data(self) -> TracerData:
        functions: List[FunctionData] = []

        for key, total_time in self._func_time.items():
            calls = self._func_calls[key]
            avg_time = total_time / calls if calls else 0
            functions.append(
                FunctionData(
                    name = key,
                    total_time = total_time,
                    call_count = calls,
                    avg_time = avg_time,
                    callees = {k for k in self._call_map.get(key, {}).keys()},
                )
            )

        metadata: TracerMetadata = TracerMetadata(
            root_path = self._root_path,
            total_functions = len(functions),
            total_execution_time = self._total_time,
        )

        return TracerData(
            metadata=metadata,
            functions=functions,
        )


_tracer_instance: Optional[Tracer] = None


def start_trace(root_dir: str) -> None:
    # Starts tracer instance
    global _tracer_instance
    if _tracer_instance is not None:
        print("[yellow]Tracer is already running.[/]")
        return
    _tracer_instance = Tracer(root_dir)
    _tracer_instance.start()


def stop_trace() -> Optional[TracerData]:
    # Stops tracer instance
    global _tracer_instance
    if _tracer_instance:
        _tracer_instance.stop()
        data = _tracer_instance.get_trace_data()
        _tracer_instance = None
        return data
    else:
        print("[yellow]Tracer was not started.[/]")
        return None


def show_results(top: Optional[int]) -> None:
    # Show results from global tracer instance
    global _tracer_instance
    if _tracer_instance:
        _tracer_instance.show_results(top)
    else:
        print("[yellow]Tracer was not started.[/]")
