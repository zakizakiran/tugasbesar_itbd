#!/usr/bin/env python3
import sys
import csv

sum_count = {}  # cat -> [sum, count]

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    cat, rating = line.split("\t", 1)
    try:
        r = int(rating)
    except:
        continue

    if cat not in sum_count:
        sum_count[cat] = [0, 0]
    sum_count[cat][0] += r
    sum_count[cat][1] += 1

rows = []
for cat, (s, c) in sum_count.items():
    avg = s / c if c else 0.0
    rows.append((cat, avg, c))

# sort by avg desc
rows.sort(key=lambda x: x[1], reverse=True)

writer = csv.writer(sys.stdout)
writer.writerow(["category", "avg_rating", "review_count"])
for cat, avg, c in rows:
    writer.writerow([cat, f"{avg:.2f}", c])
