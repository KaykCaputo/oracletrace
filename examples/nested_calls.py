import math


def parse_line(line: str) -> dict:
    parts = line.strip().split(",")
    return {"x": float(parts[0]), "y": float(parts[1])}


def distance(a: dict, b: dict) -> float:
    dx = a["x"] - b["x"]
    dy = a["y"] - b["y"]
    return math.sqrt(dx * dx + dy * dy)


def closest_pair(points: list[dict]) -> float:
    best = float("inf")
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            d = distance(points[i], points[j])
            if d < best:
                best = d
    return best


def load_data(raw: str) -> list[dict]:
    return [parse_line(line) for line in raw.strip().splitlines()]


def main() -> None:
    data = """0.0,0.0
              1.0,2.0
              3.0,1.0
              4.0,5.0
              6.0,3.0"""
    points = load_data(data)
    result = closest_pair(points)
    print(f"Closest distance: {result:.4f}")


if __name__ == "__main__":
    main()
