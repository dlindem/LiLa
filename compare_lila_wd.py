import csv, json

# Found 1788958
# 985148 not found

with open("wikidata_tLOkeO.csv") as file:
    csvrows = csv.DictReader(file, delimiter=",")
    wikidata = {}
    for row in csvrows:
        wikidata[row['lila_link'].replace('https://lila-erc.eu/lodview/data/id/lemma/','')] = {
            'lemma': row['lemma'],
            'form_rep': row['form_rep'],
            'form_uri': row['form'],
            'gramm_feat': row['gramm'].split(' ')
        }

print("Data from Wikidata loaded to memory")

with open("enhanced_forms.csv") as file:
    csvrows = csv.DictReader(file, delimiter=",")
    found = []
    not_found = []
    for row in csvrows:
        if row['lila_id_lemma'] in wikidata:
            if row['lila_id_lemma'] not in found:
                found.append(row['lila_id_lemma'])
        else:
            if row['lila_id_lemma'] not in not_found:
                not_found.append(row['lila_id_lemma'])

with open('intersection_lilamorph_wikidata.json', 'w') as file:
    json.dump(found, file, indent=2)
with open('lilamorph_missing_in_wikidata.json', 'w') as file:
    json.dump(not_found, file, indent=2)

