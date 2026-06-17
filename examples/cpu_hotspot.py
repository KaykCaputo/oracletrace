import math


def count_factors(n: int) -> int:
    count = 0
    for i in range(1, int(math.isqrt(n)) + 1):
        if n % i == 0:
            count += 1
            if i != n // i:
                count += 1
    return count


def find_highly_composite(limit: int) -> int:
    best = 0
    best_count = 0
    for n in range(1, limit + 1):
        c = count_factors(n)
        if c > best_count:
            best_count = c
            best = n
    return best, best_count


def main() -> None:
    n, c = find_highly_composite(5000)
    print(f"Most composite: {n} with {c} factors")


if __name__ == "__main__":
    main()
