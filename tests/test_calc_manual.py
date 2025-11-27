from src.calculations import calculate_item, summarize_invoice

item1 = calculate_item(240, 700, 18)   # matches your sample invoice row
item2 = calculate_item(144, 700, 18)

items = [item1 | {"qty": 240}, item2 | {"qty": 144}]
summary = summarize_invoice(items)

print("Item1:", item1)
print("Item2:", item2)
print("Summary:", summary)
