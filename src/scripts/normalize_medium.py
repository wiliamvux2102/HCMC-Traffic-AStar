from src.traffic.normalizer import normalize_here_file


INPUT = (
    "data/traffic/coverage_tests/"
    "2026-10-03/"
    "00-14-06-medium.json"
)

OUTPUT = (
    "data/traffic/normalized/"
    "2026-10-03/"
    "00-14-06-medium-here.csv"
)


df = normalize_here_file(
    INPUT,
    OUTPUT
)

print()
print("Normalized rows:", len(df))