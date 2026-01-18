import sys, csv, re

reader = csv.reader(sys.stdin)
header = next(reader, None)
if not header:
    sys.exit(0)

text_idx = header.index("text")

for row in reader:
    try:
        text = row[text_idx].lower()
        text = re.sub(r'[^a-z\s]', ' ', text)
        for w in text.split():
            if len(w) > 2:
                print(f"{w}\t1")
    except:
        pass
