import csv


# get unique lila lemma ID from prinparlat big file
print("Reading prinparlat forms...")
with open("../data/enhanced_forms.csv") as file:
    csvrows = csv.DictReader(file, delimiter=",")
    cell_forms = []
    for row in csvrows:
        cell_forms.append(row['cell'])
    print("Getting uniques...")
    cell_types = set(cell_forms)

with open("../data/leipzig_cell_types_verbs.txt", "w") as file:
    file.write("\n".join(list(cell_types)))