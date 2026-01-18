import sys, csv

reader = csv.reader(sys.stdin)
header = next(reader, None)
if not header:
    sys.exit(0)

cat_idx = header.index("category")

for row in reader:
    try:
        cat = row[cat_idx].strip()
        if cat:
            print(f"{cat}\t1")
    except:
        pass
