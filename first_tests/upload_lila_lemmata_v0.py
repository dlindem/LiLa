import csv, sys, time, re

# sparql wrapper for LiLa endpoint
from SPARQLWrapper import SPARQLWrapper, JSON
sparql = SPARQLWrapper("https://lila-erc.eu/sparql/lila_knowledge_base/sparql")

# wikibaseintegrator for lilamorph wikibase
from wikibaseintegrator import WikibaseIntegrator, wbi_login, datatypes
from wikibaseintegrator.wbi_config import config
import config_private # bot user and pwd from hidden file
config['MEDIAWIKI_API_URL'] = "https://lilamorph.wikibase.cloud/w/api.php"
config['USER_AGENT'] = "upload_prinparlat_lemmata.py"
lilamorph = WikibaseIntegrator(login=wbi_login.Login(user=config_private.wbuser, password=config_private.wbpwd))

# get unique lila lemma ID from prinparlat big file
print("Reading prinparlat forms...")
with open("data/enhanced_forms.csv") as file:
    csvrows = csv.DictReader(file, delimiter=",")
    flexeme_ids = []
    for row in csvrows:
        if "#DEF#" in str(row): # In some rows, this appears - lines are skipped
            continue
        try:
            flexeme_ids.append(int(row['lila_id_lemma'])) # In some rows, instead of a single lila_id convertible to int, there appears a python list (always ['114215', '114214']) - lines are skipped
        except Exception as ex:
            print(str(ex))
    print(f"Got lila lemma ID from {len(flexeme_ids)} csv rows.")
    flexeme_unique_ids = set(flexeme_ids)
    print(f"That is {len(flexeme_unique_ids)} unique IDs.")
    flexeme_unique_ids_sorted = sorted(flexeme_unique_ids)

# read mappingfile (lexemes created in former runs of the script)
with open("mappings/prinparlat_wikibase_mapping_flexemes.csv", "r") as mappingfile:
    mappingrows = mappingfile.read().split("\n")
    done_flexeme_ids = []
    for row in mappingrows:
        done_lila_id_re = re.search(r"^\d+", row)
        if done_lila_id_re:
            done_flexeme_ids.append(int(done_lila_id_re.group(0)))
    print(f"{len(done_flexeme_ids)} LiLa ID have been processed in former runs:\n{done_flexeme_ids}")

with open("mappings/prinparlat_wikibase_mapping_flexemes.csv", "a") as mappingfile:
    for lila_id in flexeme_unique_ids_sorted:
        if lila_id in done_flexeme_ids:
            continue
        # get lemma from lila
        query = "prefix lemma: <http://lila-erc.eu/data/id/lemma/>"
        query += "SELECT ?lemma WHERE {"
        query += f"lemma:{lila_id} ontolex:writtenRep ?lemma."
        query += "}"
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        done = False
        while not done:
            try:
                ret = sparql.queryAndConvert()
                lemma = ret["results"]["bindings"][0]["lemma"]["value"] # TODO solve PROBLEM: There is sometimes more than one ontolex:writtenRep
                done = True
            except Exception as ex:
                print(ex)
                time.sleep(2)
        print(f"Found lemma {lemma} on LiLa for lemma_id {lila_id}")
        # build and write new lexeme
        new_lexeme = lilamorph.lexeme.new(language="Q3", lexical_category="Q5") # latin verb
        new_lexeme.lemmas.set(language="la", value=lemma)
        new_lexeme.claims.add(datatypes.ExternalID(prop_nr="P1", value=f"lemma/{lila_id}"))
        new_lexeme.write()
        mappingfile.write(f"{lila_id}\t{new_lexeme.id}\n")
        print(f"Sucessfully created Lexeme https://lilamorph.wikibase.cloud/entity/{new_lexeme.id}")
        time.sleep(0.5)
        sys.exit()


