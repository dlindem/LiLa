import csv, sys, time, re, json

# wikibaseintegrator for lilamorph wikibase
from wikibaseintegrator import WikibaseIntegrator, wbi_login, datatypes
from wikibaseintegrator.models import Reference, References, Form, Sense
from wikibaseintegrator.wbi_config import config
import config_private # bot user and pwd from hidden file
config['MEDIAWIKI_API_URL'] = "https://lilamorph.wikibase.cloud/w/api.php"
config['USER_AGENT'] = "upload_prinparlat_lemmata.py"
print("Getting logged into lilamorph wikibase...")
lilamorph = WikibaseIntegrator(login=wbi_login.Login(user=config_private.wbuser, password=config_private.wbpwd))

# get prinparlat cell descriptors mapping
with open("data/leipzig_wikibase_mapping.csv") as file:
    mappingrows = csv.reader(file, delimiter="\t")
    leipzig_qid = {}
    for row in mappingrows:
        leipzig_qid[row[0]] = row[1]
print(f"Leipzig cell descriptors mapping: {leipzig_qid}")

# get prinparlat cell types default order
with open("data/leipzig_celltypes_sorted.txt") as file:
    celltypes_sorted = file.read().split("\n")
cellfeatures = {}
for celltype in celltypes_sorted:
    cellfeatures[celltype] = []
    for val in celltype.split("."):
        cellfeatures[celltype].append(leipzig_qid[val])
print(f"cellfeatures dict: {cellfeatures}")

# get prinparlat cell types default order
with open("data/prinparlat_lexemes_canonical_forms.csv") as file:



# # get unique lila lemma ID from prinparlat big file
# print("Reading prinparlat forms...")
# with open("enhanced_forms.csv") as file:
#     csvrows = csv.DictReader(file, delimiter=",")
#     flexeme_ids = []
#     for row in csvrows:
#         if "#DEF#" in str(row): # Defectives in irregulars (e.g. deponents) - lines are skipped
#             continue
#         try:
#             flexeme_ids.append(row['flexeme']) # In some rows, instead of a single lila_id convertible to int, there appears a python list (always ['114215', '114214']) - lines are skipped
#         except Exception as ex:
#             print(str(ex))
#     print(f"Got prinparlat flexeme ID from {len(flexeme_ids)} csv rows.")
#     flexeme_unique_ids = set(flexeme_ids)
#     print(f"That is {len(flexeme_unique_ids)} unique IDs.")
#     flexeme_unique_ids_sorted = sorted(flexeme_unique_ids)

# read mappingfile (lexemes created in former runs of the script)
with open("mappings/prinparlat_wikibase_mapping_flexemes.csv", "r") as mappingfile:
    mappingrows = csv.DictReader(mappingfile, delimiter="\t")
    done_flexeme_ids = []
    for row in mappingrows:
        done_flexeme_ids.append(row['flexeme'])
    print(f"{len(done_flexeme_ids)} flexeme IDs have been processed in former runs:\n{done_flexeme_ids}")

# build forms dictionary
with open("data/enhanced_forms.csv") as file:
    not_found = 0
    csvrows = csv.DictReader(file, delimiter=",")
    flexemes = {}
    for row in csvrows:
        flexeme_id = row['flexeme']
        if flexeme_id not in flexemes:
            flexemes[flexeme_id] = {}
        flexemes[flexeme_id][row['cell']] = row
    print(f"Flexemes lexicon built ({len(flexemes)} flexemes).")

for flexeme in flexemes:
    print(f"\nNow processing flexeme: {flexeme}")
    if flexeme in done_flexeme_ids:
        print(f"{flexeme} flexeme has been done before (found in mappingfile), skipped.")
        continue
    if "prs.act.ind.1.sg" not in flexemes[flexeme] or "prs.pass.ind.1.sg" not in flexemes[flexeme]:
        print(f"flexeme {flexeme} has no 1.p. in present, skipped in this run.")
        with open("data/enhanced_forms_skipped_flexemes_flexemes_upload.txt", "a") as logfile:
            logfile.write(f"{flexeme}\n")
        continue
    rowcount = 0
    wikibase_lemma = None
    new_lexeme = None
    # ask for forms data from the formypes (celltypes) canonical order list
    for celltype in celltypes_sorted:
        if celltype in flexemes[flexeme]:
            rowcount += 1
            rowdata = flexemes[flexeme][celltype]

            if not new_lexeme: #create flexeme entry
                new_lexeme = lilamorph.lexeme.new(language="Q3", lexical_category="Q5")  # latin verb
                new_lexeme.claims.add(datatypes.ExternalID(prop_nr="P6", value=flexeme))
                new_lexeme.claims.add(datatypes.ExternalID(prop_nr="P8", value=rowdata['lexeme']))
                new_lexeme.claims.add(datatypes.ExternalID(prop_nr="P1", value=f"lemma/{rowdata['lila_id_lemma']}"))

            if rowdata['form_normalized'] == "#DEF#": # do not write rows with that to Wikibase
                continue
            if not wikibase_lemma and celltype == "prs.act.ind.1.sg":
                wikibase_lemma = rowdata['form_normalized']
                print(f"Row {rowcount}: Found for lemma cell {celltype}: {rowdata['form_normalized']}")
            if not wikibase_lemma and celltype == "prs.pass.ind.1.sg":
                wikibase_lemma = rowdata['form_normalized']
                print(f"Row {rowcount}: Found for lemma cell {celltype}: {rowdata['form_normalized']}")


            # Create form

            form = Form()
            form.representations.set(language='la', value=rowdata['form_normalized'])
            form.grammatical_features = cellfeatures[celltype]
            form.claims.add(datatypes.MonolingualText(prop_nr="11", language="la", text=rowdata['orth_form']))
            form.claims.add(datatypes.String(prop_nr="12", value=rowdata['analysed_orth_form']))
            form.claims.add(datatypes.String(prop_nr="13", value=celltype))
            new_lexeme.forms.add(form)

    if not wikibase_lemma:
        print(f"flexeme {flexeme} has only #DEF# in 1.p. present, skipped in this run.")
        with open("data/enhanced_forms_skipped_flexemes_flexemes_upload.txt", "a") as logfile:
            logfile.write(f"{flexeme}\n")
        continue
    new_lexeme.lemmas.set(language="la", value=wikibase_lemma)
    # with open("test_flexeme_entry.json", "w") as jsonfile:
    #     json.dump(new_lexeme.get_json(), jsonfile, indent=2)
    new_lexeme.write()
    with open("mappings/prinparlat_wikibase_mapping_flexemes.csv", "a") as mappingfile:
        mappingfile.write(f"{rowdata['flexeme']}\t{rowdata['lexeme']}\t{rowdata['lila_id_lemma']}\t{new_lexeme.id}\n")
    print(f"Sucessfully created Lexeme https://lilamorph.wikibase.cloud/entity/{new_lexeme.id} and added {rowcount} forms.")
    time.sleep(0.34)
sys.exit()
