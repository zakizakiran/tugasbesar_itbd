import sys, csv

reader = csv.reader(sys.stdin)
header = next(reader, None)
if not header:
    sys.exit(0)

prod_idx = header.index("product_name")
rating_idx = header.index("rating")

for row in reader:
    try:
        rating = int(row[rating_idx])
        if rating <= 2:
            product = row[prod_idx].strip()
            if product:
                print(f"{product}\t1")
    except:
        pass
