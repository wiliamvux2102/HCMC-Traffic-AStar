import pandas as pd


NODES_PATH = (
    "data/processed/"
    "nodes.csv"
)


df = pd.read_csv(
    NODES_PATH
)


west = df["longitude"].min()
east = df["longitude"].max()

south = df["latitude"].min()
north = df["latitude"].max()


print("Graph bounds:")
print("west :", west)
print("south:", south)
print("east :", east)
print("north:", north)

print()
print(
    f"BBOX = {west},{south},{east},{north}"
)