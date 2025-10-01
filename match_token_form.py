import csv

import pandas as pd
import time

data = pd.read_csv("ITTB_lemmata_wikibase.csv", sep="\t")
length = data.shape[0]
rowcount = 1
thislemma = None
lemmadict = {}
while rowcount < length:
    rowdata = data.iloc[rowcount].to_dict()
    # print(rowdata)
    lila_lemma = str(rowdata['lila_lemma_id'])
    if lila_lemma != thislemma: # new lemma list begins
        thislemma = lila_lemma
        lemmadict[thislemma] = [rowdata]
    else:
        lemmadict[thislemma].append(rowdata)
    rowcount += 1

# print(list(lemmadict.keys()))

with open("ITTB_verb_tokendata.csv") as file:
    tokenrows = csv.DictReader(file, delimiter="\t")
    for row in tokenrows:
        # print(f"Now processing lemma ID: {row['lila_lemma']}...")
        if str(row['lila_lemma']) not in lemmadict:
            continue
        lemmadict_entry = lemmadict[row['lila_lemma']]
        token_features = row['features'].split("|")
        for formdata in lemmadict_entry:
            if sorted(token_features) == sorted(formdata['udp_list'].split("|")):
                print(f"Found match: token {row['tokenLabel']} = {formdata['formrep']}")























# query = """PREFIX wdt: <http://www.wikidata.org/prop/direct/>
#         PREFIX lmwb: <https://lilamorph.wikibase.cloud/entity/>
#         PREFIX lmdp: <https://lilamorph.wikibase.cloud/prop/direct/>
#
#         select distinct ?flexeme ?form ?formrep
#         (group_concat(distinct ?udp;SEPARATOR="|") as ?udp_list)
#         where {
#           ?flexeme lmdp:P1 'lemma/""" + str(lemma_id) + """'.
#           ?flexeme ontolex:lexicalForm ?form.
#           ?form ontolex:representation ?formrep; wikibase:grammaticalFeature ?form_feat.
#           ?form_feat lmdp:P9 [lmdp:P7 ?udp] .
#         } group by ?flexeme ?lemma_id ?form ?formrep ?udp_list"""