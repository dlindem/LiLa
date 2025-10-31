import csv, sys, time, re, json, requests
import config_private # bot user and pwd from hidden file

import mwclient # mediawiki api client

lilamorph_api = mwclient.Site('lilamorph.wikibase.cloud')
login = lilamorph_api.login(username=config_private.wbuser, password=config_private.wbpwd)
csrfquery = lilamorph_api.api('query', meta='tokens')
lilamorph_api_token = csrfquery['query']['tokens']['csrftoken']
print("Got fresh CSRF token for lilamorph.wikibase.cloud.")

with open("mappings/lilalemmas_inflectiontypes_qids.csv") as file:
    mappingrows = csv.DictReader(file, delimiter="\t")
    inftype_qid = {}
    for row in mappingrows:
        inftype_qid[row['lila_lemma']] = row['inftype_qid']
# print(f"Inflection types qid mapping: {inftype_qid}")

with open("data/lila_lemma_statements.csv") as file:
    rows = csv.DictReader(file, delimiter="\t")
    count = 0
    for row in rows:
        count += 1
        qid = inftype_qid[row['lila_lemma_id']]
        statement_id = row['linked_lila_st']
        statement_qid = re.search(r'^Q\d+', statement_id).group(0)
        qualivalue = json.dumps({"entity-type": "item", "numeric-id": int(qid.replace("Q", ""))})
        print(f"Will write inftype {qid} to statement {statement_id} with value {row['lila_lemma_id']}")
        attempts = 0
        while attempts < 3:
            attempts += 1
            setqualifier = lilamorph_api.post('wbsetqualifier', token=lilamorph_api_token, claim=statement_id,
                                     property="P22", snaktype="value", value=qualivalue, bot=1)
            time.sleep(.34)
            if setqualifier['success'] == 1:
                print(f"Success writing to https://lilamorph.wikibase.cloud/entity/{statement_qid}")
                break
        if attempts == 3:
            print(f"Failing to write to Wikibase.")
            sys.exit()

print("\nFinished.")

#
# PREFIX lmwb: <https://lilamorph.wikibase.cloud/entity/>
# PREFIX lmdp: <https://lilamorph.wikibase.cloud/prop/direct/>
# PREFIX lmp: <https://lilamorph.wikibase.cloud/prop/>
# PREFIX lmps: <https://lilamorph.wikibase.cloud/prop/statement/>
# PREFIX lmpq: <https://lilamorph.wikibase.cloud/prop/qualifier/>
#
# select distinct ?token ?linked_lila_st ?lila_lemma_id ?inftype
#
# where { values ?lexicon {lmwb:Q15} # Prinparlat lexemes collection version 3
#   ?token lmdp:P14 lmwb:Q13; rdfs:label ?token_label. # in collection ITTB
#        filter(lang(?token_label)="la")
#   ?token lmp:P16 ?linked_lila_st.
#        ?linked_lila_st lmps:P16 ?lila_lemma_id.
#      filter not exists { ?linked_lila_st lmpq:P22 ?inftype. }
#
# }
# order by ?token