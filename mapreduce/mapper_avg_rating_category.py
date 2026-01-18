#!/usr/bin/env python3
import sys, csv

reader = csv.reader(sys.stdin)
header = next(reader, None)
if not header:
    sys.exit(0)

cat_idx = header.index("category")
rating_idx = header.index("rating")

for row in reader:
    try:
        cat = row[cat_idx].strip()
        rating = int(row[rating_idx])
        print(f"{cat}\t{rating}")
    except:
        pass
