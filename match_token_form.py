import csv
import time
import config_private
from wikibaseintegrator import WikibaseIntegrator, wbi_login
from wikibaseintegrator.wbi_config import config
from wikibaseintegrator.wbi_helpers import execute_sparql_query

config['MEDIAWIKI_API_URL'] = "https://lilamorph.wikibase.cloud/w/api.php"
config['USER_AGENT'] = "upload_prinparlat_lexemes.py"
config['SPARQL_ENDPOINT_URL'] = "https://lilamorph.wikibase.cloud/query/sparql"
print("Getting logged into lilamorph wikibase...")
lilamorph = WikibaseIntegrator(login=wbi_login.Login(user=config_private.wbuser, password=config_private.wbpwd))
print("Login successful.")


def get_wikibase_forms(lila_lemma_id):
    query = """PREFIX lmwb: <https://lilamorph.wikibase.cloud/entity/>
        PREFIX lmdp: <https://lilamorph.wikibase.cloud/prop/direct/>
        PREFIX lmp: <https://lilamorph.wikibase.cloud/prop/>
        PREFIX lmps: <https://lilamorph.wikibase.cloud/prop/statement/>
        PREFIX lmpq: <https://lilamorph.wikibase.cloud/prop/qualifier/>
        
         select distinct 
            ?lila_lemma_id (group_concat(distinct ?lila_id_linked_flexeme_id;SEPARATOR="|") as ?lila_id_linked_flexeme_ids)
            ?form (group_concat(distinct ?form_flexeme_id;SEPARATOR="|") as ?form_flexeme_ids) ?form_rep 
            (group_concat(distinct ?udp_label;SEPARATOR="|") as ?udp_list)
                      
             where { values ?lila_lemma_id { """ + f'"{lila_lemma_id}"' + """ }
          ?lexeme lmdp:P14 lmwb:Q15; lmp:P1 ?lila_st.
               ?lila_st lmps:P1 ?lila_lemma_id; lmpq:P6 ?lila_id_linked_flexeme_id.
          ?lexeme ontolex:lexicalForm ?form.
          ?form lmdp:P6 ?form_flexeme_id; ontolex:representation ?form_rep; wikibase:grammaticalFeature [lmdp:P9 [lmdp:P7 ?udp_label]].
               
          } group by ?lila_lemma_id ?lexeme ?form ?form_rep ?count ?flexemes order by desc(?count)"""
    # print(query)

    bindings = execute_sparql_query(query=query)['results']['bindings']
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
    tokenrowcount = 0
    for row in tokenrows:
        tokenrowcount += 1

        match_for_token = False
        lila_lemmas = row['lila_lemmas'].split("|")  # matching lila lemma(s), according to token annotation

        print(f"\n[{tokenrowcount}] Now processing lemma IDs: {lila_lemmas}...")
        for lila_lemma in lila_lemmas:

            if lila_lemma not in lemmadict:
                print(f"Retrieving form data for LiLa Lemma '{lila_lemma}' from Wikibase...")
                lemmadict[lila_lemma] = get_wikibase_forms(lila_lemma)

            if len(lemmadict[lila_lemma]) == 0:
                print("Did not find this lemma on Wikibase.")
                with open('data/lemma_not_found_lexemedict_v3.csv', 'a') as outfile:
                    outfile.write(f"{lila_lemma}\n")
                continue

            token_features = sorted(row['features'].split("|"))
            # for ignore_feature in ["VerbForm#Fin", "Degree#Pos", "Aspect#Imp"]:
            #     if ignore_feature in token_features:
            #         token_features.remove(ignore_feature)

            # matching algorithm
            for formdata in lemmadict[lila_lemma]:
                form_features = sorted(formdata['udp_list']['value'].split("|"))

                for form_flex_id in formdata['form_flexeme_ids']['value'].split("|"):
                    if form_flex_id not in formdata['lila_id_linked_flexeme_ids']['value'].split("|"):
                        continue  # do not look at forms that do not have a flexeme id associated to the lila lemma
                        # example: https://lilamorph.wikibase.cloud/wiki/Lexeme:L33585
                if formdata['form_rep']['value'] == row['tokenLabel'].replace("v", "u"):
                    # match according to form representation
                    for ignore_feature in ["Aspect#Imp"]:  # those that are not coherently there (on the tokens)
                        if ignore_feature in form_features:
                            form_features.remove(ignore_feature)
                    # check if morph annotation is also matching
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
                        with open('data/matching_tokens_lexemedict_v3.csv', 'a') as outfile:
                            outfile.write(
                                f"{row['token']}\t{row['tokenLabel']}\t{token_items[row['token']]}\t{formdata['form']['value']}\t{lila_lemma}\t{'|'.join(token_features)}\n")

        if not match_for_token:
            with open('data/not_matching_tokens_lexemedict_v3.csv', 'a') as outfile:
                outfile.write(
                    f"{row['token']}\t{row['tokenLabel']}\tNO MATCH\t{lila_lemma}\t{'|'.join(token_features)}\n")

print(f"\nFound {matchcount} matches.")
