import csv, time, sys
import config_private
import mwclient # mediawiki api client (will be used for itemdata > 1MB
lilamorph_api = mwclient.Site('lilamorph.wikibase.cloud')
login = lilamorph_api.login(username=config_private.wbuser, password=config_private.wbpwd)
csrfquery = lilamorph_api.api('query', meta='tokens')
lilamorph_api_token = csrfquery['query']['tokens']['csrftoken']
print("Got fresh CSRF token for lilamorph.wikibase.cloud.")

with open('mappings/lilalemmas_inflectiontypes.csv') as file:
    rows = csv.DictReader(file, delimiter="\t")
    inftypes = {}
    for row in rows:
        inftypes[row['lila_lemma']] = row['lila_inftype']

with open('mappings/lila_inflection_types_mapping.csv') as file:
    rows = csv.DictReader(file, delimiter="\t")
    inftype_qids = {}
    for row in rows:
        inftype_qids[row['lila_inftype']] = row['lilamorph_qid']

mapping = ""
with open('mappings/lila_verbs_wikibase.csv') as file:
    rows = csv.DictReader(file, delimiter=",")
    count = 0
    for row in rows:
        count += 1
        print(f"\n[{count}] Now processing row {row}")
        inftype = inftypes[row['lila_lemma_id']]
        inftype_qid = inftype_qids[inftype]
        print(f"Inftype will be {inftype} - {inftype_qid}")
        mapping += f"{row['lexeme']}\tP22\t{inftype_qid}\n"

with open('data/inftypes_for_upload.csv', 'w') as file:
    file.write(mapping)