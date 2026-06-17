import os


def fast_prefix_sum(arr: list[int]) -> list[int]:
    result = []
    total = 0
    for x in arr:
        total += x
        result.append(total)
    return result


def slow_prefix_sum(arr: list[int]) -> list[int]:
    return [sum(arr[: i + 1]) for i in range(len(arr))]


def main() -> None:
    data = list(range(1, 2000))
    if os.environ.get("SLOW") == "1":
        result = slow_prefix_sum(data)
    else:
        result = fast_prefix_sum(data)
    print(f"Sum: {result[-1]}")


if __name__ == "__main__":
    main()
