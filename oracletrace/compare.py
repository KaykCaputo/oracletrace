from rich import print


def compare_traces(old_data, new_data, threshold=5.0):
    old_funcs = {f["name"]: f for f in old_data["functions"]}
    new_funcs = {f["name"]: f for f in new_data["functions"]}

    regressions = []

    print("\n[bold cyan]Comparison Results:[/]\n")

    all_functions = set(old_funcs) | set(new_funcs)

    for name in sorted(all_functions):
        old = old_funcs.get(name)
        new = new_funcs.get(name)

        if not old:
            print(f"[green]+ {name} (new function)[/]")
            continue

        if not new:
            print(f"[red]- {name} (removed)[/]")
            continue

        old_time = old["total_time"]
        new_time = new["total_time"]

        if old_time == 0:
            continue

        diff = new_time - old_time
        percent = (diff / old_time) * 100

        color = "red" if percent > threshold else "green" if percent < -threshold else "yellow"

        print(
            f"{name}\n"
            f"    total_time: {old_time:.4f}s → {new_time:.4f}s "
            f"[{color}]({percent:+.2f}%)[/]\n"
        )

        if percent > threshold:
            regressions.append(
                {
                    "name": name,
                    "old_time": old_time,
                    "new_time": new_time,
                    "percent": percent,
                }
            )

    return {
        "regressions": regressions,
        "has_regression": len(regressions) > 0,
    }
