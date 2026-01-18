import sys
import csv
import os

TOPN = int(os.environ.get("TOPN", "50"))

counts = {}
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    key, val = line.split("\t", 1)
    try:
        counts[key] = counts.get(key, 0) + int(val)
    except:
        continue


top_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:TOPN]

writer = csv.writer(sys.stdout)
header = os.environ.get("HEADER", "")
if header:
    writer.writerow([h.strip() for h in header.split(",")])

for k, c in top_items:
    writer.writerow([k, c])