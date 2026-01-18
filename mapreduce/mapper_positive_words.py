import sys, csv, re

reader = csv.reader(sys.stdin)
header = next(reader, None)
if not header:
    sys.exit(0)

text_idx = header.index("text")
rating_idx = header.index("rating")

for row in reader:
    try:
        rating = int(row[rating_idx])
        if rating >= 4:
            text = re.sub(r'[^a-z\s]', ' ', row[text_idx].lower())
            for w in text.split():
                if len(w) > 2:
                    print(f"{w}\t1")
    except:
        pass
