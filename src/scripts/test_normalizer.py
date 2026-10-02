from src.traffic.normalizer import (
    normalize_here_file
)


INPUT = (
    "data/traffic/raw/"
    "2026-10-02/"
    "16-57-46-here.json"
)

OUTPUT = (
    "data/traffic/normalized/"
    "2026-10-02/"
    "16-57-46-here.csv"
)


df = normalize_here_file(
    INPUT,
    OUTPUT
)


print()
print(df.head())

print()
print(df.info())

print()
print(
    df[
        [
            "description",
            "length_m",
            "speed_kph",
            "free_flow_kph",
            "jam_factor",
            "confidence"
        ]
    ].head(10)
)

import pandas as pd

df = pd.read_csv(
    "data/traffic/normalized/2026-10-02/16-57-46-here.csv"
)

print(
    "speed <= 0:",
    (df["speed_kph"] <= 0).sum()
)

print(
    "confidence range:",
    df["confidence"].min(),
    df["confidence"].max()
)

print(
    "closed segments:",
    (df["traversability"] != "open").sum()
)

print(
    "speed > free flow:",
    (
        df["speed_kph"]
        > df["free_flow_kph"]
    ).sum()
)