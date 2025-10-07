import csv

import pandas as pd
import time

data = pd.read_csv("data/lemmata_wikibase.csv", sep="\t")
length = data.shape[0]
rowcount = 1
thislemma = None
lemmadict = {}
while rowcount < length:
    rowdata = data.iloc[rowcount].to_dict()
    # print(rowdata)
    lila_lemma = str(rowdata['lila_lemma_id']).replace("lemma/","")
    if lila_lemma != thislemma: # new lemma list begins
        thislemma = lila_lemma
        lemmadict[thislemma] = [rowdata]
    else:
        lemmadict[thislemma].append(rowdata)
    rowcount += 1

# print(list(lemmadict.keys()))

matchcount = 0
with open("data/ITTB_verb_tokendata.csv") as file:
    tokenrows = csv.DictReader(file, delimiter="\t")
    for row in tokenrows:
        # print(f"Now processing lemma ID: {row['lila_lemma']}...")
        if str(row['lila_lemma']) not in lemmadict:
            continue
        lemmadict_entry = lemmadict[row['lila_lemma']]
        token_features = sorted(row['features'].split("|"))
        # for ignore_feature in ["VerbForm#Fin", "Degree#Pos", "Aspect#Imp"]:
        #     if ignore_feature in token_features:
        #         token_features.remove(ignore_feature)

        for formdata in lemmadict_entry:
            form_features = sorted(formdata['udp_list'].split("|"))

            if formdata['formrep'] == row['tokenLabel'].replace("v", "u"):

                for ignore_feature in ["Aspect#Imp"]:
                    if ignore_feature in form_features:
                        form_features.remove(ignore_feature)

                match = True
                for feature in form_features:
                    if feature not in token_features:
                        match = False

                if match:
                    matchcount += 1
                    print(f"\nMatching token: {row['tokenLabel']} {token_features}\nMatching form:  {formdata['formrep']} {form_features}")

print(f"\nFound {matchcount} matches.")





















query = """PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX lmwb: <https://lilamorph.wikibase.cloud/entity/>
        PREFIX lmdp: <https://lilamorph.wikibase.cloud/prop/direct/>

        select distinct ?lila_lemma_id ?flexeme ?form ?formrep
        (group_concat(distinct ?udp;SEPARATOR="|") as ?udp_list)
        where {
          ?flexeme lmdp:P1 ?lila_lemma_id.
          ?flexeme ontolex:lexicalForm ?form.
          ?form ontolex:representation ?formrep; wikibase:grammaticalFeature ?form_feat.
          ?form_feat lmdp:P9 [lmdp:P7 ?udp] .
        } group by ?lila_lemma_id ?flexeme ?form ?formrep ?udp_list"""