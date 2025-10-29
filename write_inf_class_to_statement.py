import csv, sys, time, re, json, requests
import config_private # bot user and pwd from hidden file

import mwclient # mediawiki api client

lilamorph_api = mwclient.Site('lilamorph.wikibase.cloud')
login = lilamorph_api.login(username=config_private.wbuser, password=config_private.wbpwd)
csrfquery = lilamorph_api.api('query', meta='tokens')
lilamorph_api_token = csrfquery['query']['tokens']['csrftoken']
print("Got fresh CSRF token for lilamorph.wikibase.cloud.")

with open("mappings/lilalemmas_inflectiontypes_qids.csv") as file:
    mappingrows = csv.reader(file, delimiter="\t")
    inftype_qid = {}
    for row in mappingrows:
        inftype_qid[row['lila_lemma']] = row['inftype_qid']
print(f"Inflection types qid mapping: {inftype_qid}")

with open("data/lila_lemma_statements.csv") as file:
    rows = csv.reader(file, delimiter="\t")
    count = 0
    for row in rows:
        count += 1
        qid = inftype_qid[row['lila_lemma_id']]
        print(f"Will write inftype {qid} to statement with value {row['lila_lemma_id']}")
        attempts = 0
        while attempts < 3:
            attempts += 1
            setqualifier = lilamorph_api.post('wbsetqualifier', token=lilamorph_api_token, claim=row['linked_lila_st'],
                                     property="P22", snaktype="value", value=qid, bot=1)
            time.sleep(.34)
            if setqualifier['success'] == 1:
                print("Success.")
                break

print("\nFinished.")
