import sys
import os
import time
from collections import defaultdict
from rich.tree import Tree
from rich.table import Table
from rich import print

class Tracer: 
    def __init__(self, root_dir):
        self._root_path = os.path.abspath(root_dir)
        self._call_stack = []  
        self._func_calls = defaultdict(int)
        self._func_time = defaultdict(float)
        self._call_map = defaultdict(lambda: defaultdict(int))
        self._original_profile_func = None
        self._enabled = False

    def start(self):
        #Start Tracer
        self._enabled = True
        self._original_profile_func = sys.getprofile()
        sys.setprofile(self._trace)

    def stop(self):
        #Stops Tracer
        self._enabled = False
        sys.setprofile(self._original_profile_func)

    def _is_user_code(self, filename):
        # Filter out files not in the project root
        if not filename.startswith(self._root_path):
            return False
        # Filter out third-party libraries
        if "site-packages" in filename or "dist-packages" in filename:
            return False
        return True

    def _get_key(self, frame):
        co_filename = frame.f_code.co_filename
        # Ignore internal python frames (e.g. <string>)
        if co_filename.startswith("<"):
            return None
        filename = os.path.abspath(co_filename)
        # Check if the file belongs to the user's project
        if not self._is_user_code(filename):
            return None
        # Create a relative path key for readability
        rel_path = os.path.relpath(filename, self._root_path)
        return f"{rel_path}:{frame.f_code.co_name}"

    def _trace(self, frame, event, arg):
        try:
            if not self._enabled:
                return
            
            if event == "call":
                key = self._get_key(frame)
                if not key:
                    return
                
                caller = self._call_stack[-1][1] if self._call_stack else "<module>"
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
                    fid = id(frame)
                    found = False
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

    def show_results(self):
        if not self._func_calls:
            print("[yellow]No calls traced.[/]")
            return
        
        #Summary table
        print("[bold green]Summary:[/]")
        table = Table(title="Top functions by Total Time")
        table.add_column("Function", justify="left", style="cyan", no_wrap=True)
        table.add_column("Total Time (s)", justify="right", style="magenta")
        table.add_column("Calls", justify="right", style="green")
        table.add_column("Avg. Time/Call (ms)", justify="right", style="yellow")
        
        #sort functions by time
        _sorted_by_time = sorted(self._func_time.items(), key=lambda item: item[1], reverse=True)

        for key, total_time in _sorted_by_time:
            calls = self._func_calls[key]
            avg_time_ms = (total_time/calls)* 1000 if calls > 0 else 0
            table.add_row(
                key,
                f"{total_time:.4f}",
                str(calls),
                f"{avg_time_ms:.3f}"
            )

        print(table)

        print("\n[bold green]Logic Flow:[/]")
        
        tree = Tree("[bold yellow]<module>[/]")
        
        # Recursively build the execution tree
        def add_nodes(parent_node, parent_key, current_path):
            children = self._call_map.get(parent_key, {})
            # Sort children by total execution time
            sorted_children = sorted(children.items(), key=lambda x: self._func_time.get(x[0], 0), reverse=True)
            
            for child_key, count in sorted_children:
                total_time = self._func_time[child_key]
                # Detect recursion to prevent infinite loops in the tree
                if child_key in current_path:
                    parent_node.add(f"[red]↻ {child_key}[/] ({count}x)")
                    continue
                    
                node_text = f"{child_key} [dim]({count}x, {total_time:.4f}s)[/]"
                child_node = parent_node.add(node_text)
                add_nodes(child_node, child_key, current_path | {child_key})

        add_nodes(tree, "<module>", {"<module>"})
        print(tree)



_tracer_instance = None

def start_trace(root_dir):
    #Starts tracer instance
    global _tracer_instance
    if _tracer_instance is not None:
        print("[yellow]Tracer is already running.[/]")
        return
    _tracer_instance = Tracer(root_dir)
    _tracer_instance.start()

def stop_trace():
    #Stops tracer instance
    global _tracer_instance
    if _tracer_instance:
        _tracer_instance.stop()

def show_results():
    #Show results from global tracer instance
    global _tracer_instance
    if _tracer_instance:
        _tracer_instance.show_results()
    else:
        print("[yellow]Tracer was not started.[/]")