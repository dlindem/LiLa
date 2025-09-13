import csv, sys

with open("enhanced_forms.csv") as file:
    csvrows = csv.DictReader(file, delimiter=",")
    lila_ids = []
    for row in csvrows:
        try:
            lila_ids.append(int(row['lila_id_lemma']))
        except Exception as ex:
            print(str(ex))
    print(f"Got lila lemma ID from {len(lila_ids)} csv rows.")
    lila_unique_ids = set(lila_ids)
    print(f"That is {len(lila_unique_ids)} unique IDs.")
    lila_unique_ids_sorted = sorted(lila_unique_ids)

with open("prinparlat_lemma_wikibase_mapping", "a") as file:
    for lila_id in lila_unique_ids_sorted:
        # get lemma from lila
        query = "prefix lemma: <http://lila-erc.eu/data/id/lemma/>"
        query += "SELECT ?lemma WHERE {"
        query += f"lemma:{lila_id} ontolex:writtenRep ?lemma.
        query += "}"



        new_lexeme = xwbi.wbi.lexeme.new(language="Q3", lexical_category="Q5") # latin verb


