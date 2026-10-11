import csv
import re
from collections import defaultdict

path = "data/raw/train.csv"

with open(path, encoding="utf-8", newline="") as file:
    rows = list(csv.DictReader(file))

categories = defaultdict(list)

for row in rows:
    categories[row["category"]].append(row["experience"])

for category in sorted(categories):
    print(f"\n=== {category} ===")

    for experience in categories[category][:3]:
        cleaned = re.sub(r"\s+", " ", experience).strip()
        print(cleaned[:350])