import json
from datetime import datetime
from string import Template
from typing import List
from ..tracer import TracerData, FunctionData


class _JSTemplate(Template):
    delimiter = "@"


def generate_html_report(data: TracerData, output_path: str) -> None:
    functions_json = _serialize_functions(data.functions)
    metadata = data.metadata
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = _JSTemplate(_HTML_TEMPLATE).substitute(
        root_path=metadata.root_path,
        total_time=f"{metadata.total_execution_time:.4f}s",
        total_functions=str(metadata.total_functions),
        timestamp=timestamp,
        functions_json=functions_json,
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def _serialize_functions(functions: List[FunctionData]) -> str:
    serialized = []
    for fn in functions:
        serialized.append({
            "name": fn.name,
            "total_time": fn.total_time,
            "call_count": fn.call_count,
            "avg_time": fn.avg_time * 1000,
            "callees": fn.callees,
        })
    return json.dumps(serialized)


_HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OracleTrace Report</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            padding: 20px;
            line-height: 1.5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        h1 {
            font-size: 24px;
            margin-bottom: 12px;
            color: #1a1a1a;
        }
        .meta {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            font-size: 14px;
            color: #666;
        }
        .meta-item {
            display: flex;
            flex-direction: column;
        }
        .meta-label {
            font-weight: 600;
            color: #333;
        }
        .meta-value {
            color: #1a1a1a;
        }
        .controls {
            margin-bottom: 16px;
        }
        #search {
            width: 100%;
            max-width: 400px;
            padding: 10px 14px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
        }
        #search:focus {
            outline: none;
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
        }
        .table-container {
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        th {
            text-align: left;
            padding: 12px 16px;
            background: #f8f9fa;
            border-bottom: 2px solid #e5e7eb;
            font-weight: 600;
            cursor: pointer;
            user-select: none;
            white-space: nowrap;
        }
        th:hover {
            background: #e9ecef;
        }
        th::after {
            content: " ↕";
            font-size: 12px;
            color: #999;
        }
        th.sorted-asc::after {
            content: " ↑";
            color: #2563eb;
        }
        th.sorted-desc::after {
            content: " ↓";
            color: #2563eb;
        }
        td {
            padding: 12px 16px;
            border-bottom: 1px solid #e5e7eb;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .callee {
            font-size: 12px;
            color: #666;
        }
        .footer {
            margin-top: 20px;
            text-align: center;
            font-size: 12px;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>OracleTrace Report</h1>
            <div class="meta">
                <div class="meta-item">
                    <span class="meta-label">Project</span>
                    <span class="meta-value">@root_path</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Total Time</span>
                    <span class="meta-value">@total_time</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Functions</span>
                    <span class="meta-value">@total_functions</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Generated</span>
                    <span class="meta-value">@timestamp</span>
                </div>
            </div>
        </header>
        <div class="controls">
            <input type="text" id="search" placeholder="Search functions..." autocomplete="off">
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th data-sort="name" data-dir="asc">Function</th>
                        <th data-sort="total_time" data-dir="desc">Total Time (s)</th>
                        <th data-sort="call_count" data-dir="desc">Calls</th>
                        <th data-sort="avg_time" data-dir="desc">Avg Time (ms)</th>
                        <th>Callees</th>
                    </tr>
                </thead>
                <tbody id="table-body">
                </tbody>
            </table>
        </div>
        <div class="footer">
            Generated by OracleTrace
        </div>
    </div>
    <script>
        const functions = @functions_json;

        let sortColumn = "total_time";
        let sortDir = "desc";
        let searchTerm = "";

        function render() {
            const filtered = functions.filter(f =>
                f.name.toLowerCase().includes(searchTerm.toLowerCase())
            );

            filtered.sort((a, b) => {
                const aVal = a[sortColumn];
                const bVal = b[sortColumn];
                if (aVal === bVal) return 0;
                const compareResult = aVal > bVal ? 1 : -1;
                return sortDir === "asc" ? compareResult : -compareResult;
            });

            const tbody = document.getElementById("table-body");
            tbody.innerHTML = filtered.map(f => `
                <tr>
                    <td>${f.name}</td>
                    <td>${f.total_time.toFixed(4)}</td>
                    <td>${f.call_count}</td>
                    <td>${f.avg_time.toFixed(4)}</td>
                    <td class="callee">${f.callees.join(", ")}</td>
                </tr>
            `).join("");

            document.querySelectorAll("th").forEach(th => {
                th.classList.remove("sorted-asc", "sorted-desc");
                if (th.dataset.sort === sortColumn) {
                    th.classList.add(`sorted-${sortDir}`);
                }
            });
        }

        document.querySelectorAll("th[data-sort]").forEach(th => {
            th.addEventListener("click", () => {
                const col = th.dataset.sort;
                if (sortColumn === col) {
                    sortDir = sortDir === "asc" ? "desc" : "asc";
                } else {
                    sortColumn = col;
                    sortDir = "desc";
                }
                render();
            });
        });

        document.getElementById("search").addEventListener("input", (e) => {
            searchTerm = e.target.value;
            render();
        });

        render();
    </script>
</body>
</html>
'''