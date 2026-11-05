"""Invented regression splits, exact fractions; standard library only."""
import argparse
from fractions import Fraction

HOURS = (6, 7, 8, 9, 16, 17, 18, 19)
TARGETS = (20, 30, 40, 50, 100, 110, 120, 130)


def mean(values):
    return Fraction(sum(values), len(values))


def sse(values):
    center = mean(values)
    return sum((v - center) ** 2 for v in values)


def split(threshold, targets=TARGETS):
    left = [y for h, y in zip(HOURS, targets, strict=True) if h <= threshold]
    right = [y for h, y in zip(HOURS, targets, strict=True) if h > threshold]
    return {"left_mean": mean(left), "right_mean": mean(right), "sse": sse(left) + sse(right)}


def check():
    a, b = split(Fraction(15, 2)), split(Fraction(25, 2))
    assert mean(TARGETS) == 75 and sse(TARGETS) == 13800
    assert a == {"left_mean": 25, "right_mean": Fraction(275, 3), "sse": Fraction(21400, 3)}
    assert sum(y * y for y in TARGETS[2:]) == 57500
    assert b == {"left_mean": 35, "right_mean": 115, "sse": 1000}
    assert split(Fraction(25, 2), (10, 20, 30, 40, 70, 80, 90, 100))["right_mean"] == 85
    assert mean((90, 105, 120)) == 105
    return a, b


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answers", action="store_true", help="Reveal the fresh-target checkpoint answer")
    args = parser.parse_args()
    a, b = check()
    print("INVENTED data:", list(zip(HOURS, TARGETS)))
    print("Unsplit mean=75, SSE=13800; compare total child SSE, not unweighted child MSE.")
    for threshold, result in [(7.5, a), (12.5, b)]:
        print(f"hour <= {threshold}: " + ", ".join(f"{k}={v}" for k, v in result.items()))
    print("Among these two candidates choose 12.5. Fresh hour 17 goes right: prediction=115.")
    print("Invented forest: (90+105+120)/3=105; no fitted UCI model is used here.")
    print("Checkpoint: keep threshold 12.5; replace targets with 10,20,30,40,70,80,90,100. Predict hour 17.")
    if args.answers:
        print("Answer: right training mean=(70+80+90+100)/4=85. The fresh target is unused.")


if __name__ == "__main__":
    main()
