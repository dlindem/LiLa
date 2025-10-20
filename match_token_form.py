import csv, requests
import time

# data = pd.read_csv("data/lemmata_wikibase.csv", sep="\t")
# length = data.shape[0]
# rowcount = 1
# thislemma = None
# lemmadict = {}
# while rowcount < length:
#     rowdata = data.iloc[rowcount].to_dict()
#     # print(rowdata)
#     lila_lemma = str(rowdata['lila_lemma_id']).replace("lemma/","")
#     if lila_lemma != thislemma: # new lemma list begins
#         thislemma = lila_lemma
#         lemmadict[thislemma] = [rowdata]
#     else:
#         lemmadict[thislemma].append(rowdata)
#     rowcount += 1

# print(list(lemmadict.keys()))

def get_wikibase_forms(lila_lemma_id):
    url = "https://lilamorph.wikibase.cloud/query/sparql?format=json&query=PREFIX%20rdfs%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F2000%2F01%2Frdf-schema%23%3E%0APREFIX%20ontolex%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2Fns%2Flemon%2Fontolex%23%3E%0APREFIX%20wikibase%3A%20%3Chttp%3A%2F%2Fwikiba.se%2Fontology%23%3E%0APREFIX%20lmwb%3A%20%3Chttps%3A%2F%2Flilamorph.wikibase.cloud%2Fentity%2F%3E%0APREFIX%20lmdp%3A%20%3Chttps%3A%2F%2Flilamorph.wikibase.cloud%2Fprop%2Fdirect%2F%3E%0A%0Aselect%20%3Flila_lemma_id%20%3Fform%20%3Fform_rep%20(group_concat(distinct%20%3Fudp_label%3BSEPARATOR%3D%22%7C%22)%20as%20%3Fudp_list)%0A%20%20%20%20%20%20%20%0Awhere%20%7B%20bind(%27lemma%2F"+lila_lemma_id+"%27%20as%20%3Flila_lemma_id)%0A%20%20%3Flexeme%20lmdp%3AP1%20%3Flila_lemma_id%3B%20lmdp%3AP14%20lmwb%3AQ14%3B%20ontolex%3AlexicalForm%20%3Fform.%0A%20%20%3Fform%20ontolex%3Arepresentation%20%3Fform_rep%3B%20wikibase%3AgrammaticalFeature%20%5Blmdp%3AP9%20%3Fudp_map%5D.%20%3Fudp_map%20rdfs%3Alabel%20%3Fudp_label.%20filter%20(lang(%3Fudp_label)%3D%22en%22)%20%0A%20%20%0A%7D%20group%20by%20%3Flila_lemma_id%20%3Fform%20%3Fform_rep%20%3Fudp_list%0A%0A"
    r = requests.get(url)
    bindings = r.json()['results']['bindings']
    print(f"Got {len(bindings)} results from Wikibase SPARQL endpoint.")
    time.sleep(.3)
    return bindings

with open('mappings/ITTB_tokens_wikibase.csv') as logfile:
    token_items = {}
    rows = csv.DictReader(logfile, delimiter="\t")
    for row in rows:
        token_items[row['token_id']] = row['wikibase_qid']

lemmadict = {}
matchcount = 0
with open("data/ITTB_verb_tokendata_for_upload.csv") as file:
    tokenrows = csv.DictReader(file, delimiter="\t")
    for row in tokenrows:
        match_for_token = False
        lila_lemmas = row['lila_lemmas'].split("|") # matching lila lemma(s), according to token annotation
        for lila_lem in lila_lemmas:
            lila_lemma = lila_lem.replace("lemma/","")
            print(f"\nNow processing lemma ID: {lila_lemma}...")
            if lila_lemma not in lemmadict:
                print(f"Retrieving form data for LiLa Lemma '{lila_lemma}' from Wikibase...")
                lemmadict[lila_lemma] = get_wikibase_forms(lila_lemma)

            if len(lemmadict[lila_lemma]) == 0:
                print("Did not find this lemma on Wikibase.")
                with open('data/lemma_not_found_lexemedict_v2.csv', 'a') as outfile:
                    outfile.write(f"{lila_lemma}\n")
                    continue

            token_features = sorted(row['features'].split("|"))
            # for ignore_feature in ["VerbForm#Fin", "Degree#Pos", "Aspect#Imp"]:
            #     if ignore_feature in token_features:
            #         token_features.remove(ignore_feature)

            # matching algorithm
            for formdata in lemmadict[lila_lemma]:
                form_features = sorted(formdata['udp_list']['value'].split("|"))

                if formdata['form_rep']['value'] == row['tokenLabel'].replace("v", "u"):

                    for ignore_feature in ["Aspect#Imp"]:
                        if ignore_feature in form_features:
                            form_features.remove(ignore_feature)

                    match = True
                    for feature in form_features:
                        if feature not in token_features:
                            match = False
                            break
                    if match:
                        match_for_token = True
                        matchcount += 1
                        print(
                            f"\nMatching token: {row['tokenLabel']} {token_features}\nMatching form:  {formdata['form_rep']['value']} {form_features}")
                        with open('data/matching_tokens_lexemedict_v2.csv', 'a') as outfile:
                            outfile.write(
                                f"{row['token']}\t{row['tokenLabel']}\t{token_items[row['token']]}\t{formdata['form']['value']}\t{lila_lemma}\t{'|'.join(token_features)}\n")

            if not match_for_token:
                with open('data/not_matching_tokens_lexemedict_v2.csv', 'a') as outfile:
                    outfile.write(f"{row['token']}\t{row['tokenLabel']}\tNO MATCH\t{lila_lemma}\t{'|'.join(token_features)}\n")


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