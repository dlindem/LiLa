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
    mappingrows = csv.DictReader(file, delimiter="\t")
    canonicalforms = {}
    for row in mappingrows:
        canonicalforms[row['lexeme_id']] = row['label']
print(f"Loaded canonical forms for {len(canonicalforms)} prinparlat lemma id.")

# # get unique lila lemma ID from prinparlat big file
# print("Reading prinparlat forms...")
# with open("enhanced_forms.csv") as file:
#     csvrows = csv.DictReader(file, delimiter=",")
#     lexeme_ids = []
#     for row in csvrows:
#         if "#DEF#" in str(row): # Defectives in irregulars (e.g. deponents) - lines are skipped
#             continue
#         try:
#             lexeme_ids.append(row['lexeme']) # In some rows, instead of a single lila_id convertible to int, there appears a python list (always ['114215', '114214']) - lines are skipped
#         except Exception as ex:
#             print(str(ex))
#     print(f"Got prinparlat lexeme ID from {len(lexeme_ids)} csv rows.")
#     lexeme_unique_ids = set(lexeme_ids)
#     print(f"That is {len(lexeme_unique_ids)} unique IDs.")
#     lexeme_unique_ids_sorted = sorted(lexeme_unique_ids)

# read mappingfile (lexemes created in former runs of the script)
with open("mappings/prinparlat_wikibase_mapping_lexemes.csv", "r") as mappingfile:
    mappingrows = csv.DictReader(mappingfile, delimiter="\t")
    done_lexeme_ids = []
    for row in mappingrows:
        done_lexeme_ids.append(row['lexeme'])
    print(f"{len(done_lexeme_ids)} lexeme IDs have been processed in former runs: {done_lexeme_ids}")

# build lexemes dictionary
with open("data/enhanced_forms.csv") as file:
    not_found = 0
    csvrows = csv.DictReader(file, delimiter=",")
    lexemes = {}
    for row in csvrows:
        lexeme_id = row['lexeme']
        if lexeme_id not in canonicalforms:
            print(f"Lexeme {lexeme_id} not found in canonical forms list.")
            sys.exit()
        if lexeme_id not in lexemes:
            lexemes[lexeme_id] = {'canonical': canonicalforms[lexeme_id], 'data': {}}
        lexemes[lexeme_id]['data'][f"{row['flexeme']}@{row['cell']}"] = row # assumes that there is a unique flexeme_id@cell combination in the lexeme
    print(f"lexemes lexicon built: ({len(lexemes)} lexemes).")

for lexeme_id in lexemes:
    print(f"\nNow processing lexeme: {lexeme_id}, '{lexemes[lexeme_id]['canonical']}'")
    if lexeme_id in done_lexeme_ids:
        print(f"{lexeme_id} lexeme_idhas been done before (found in mappingfile), skipped.")
        continue

    rowcount = 0
    new_lexeme = None

    # ask for forms data from the formypes (celltypes) canonical order list
    for celltype in celltypes_sorted:
        for flexeme_cell in lexemes[lexeme_id]['data']:
            flexeme_cell_code = flexeme_cell.split("@")
            cell = flexeme_cell_code[1]
            if cell != celltype:
                continue
            rowcount += 1
            flexeme_id = flexeme_cell_code[0]
            rowdata = lexemes[lexeme_id]['data'][flexeme_cell]
            if not new_lexeme:
                new_lexeme = lilamorph.lexeme.new(language="Q3", lexical_category="Q5")  # latin verb
                new_lexeme.lemmas.set(language="la", value=lexemes[lexeme_id]['canonical'])
                new_lexeme.claims.add(datatypes.ExternalID(prop_nr="P8", value=lexeme_id))
                new_lexeme.claims.add(datatypes.ExternalID(prop_nr="P1", value=f"lemma/{rowdata['lila_id_lemma']}"))
            if rowdata['form_normalized'] == "#DEF#":  # do not write rows with that to Wikibase
                continue

            # Create form
            form = Form()
            form.representations.set(language='la', value=rowdata['form_normalized'])
            form.grammatical_features = cellfeatures[celltype]
            form.claims.add(datatypes.ExternalID(prop_nr="P6", value=flexeme_id))
            form.claims.add(datatypes.MonolingualText(prop_nr="11", language="la", text=rowdata['orth_form']))
            form.claims.add(datatypes.String(prop_nr="12", value=rowdata['analysed_orth_form']))
            form.claims.add(datatypes.String(prop_nr="13", value=celltype))
            new_lexeme.forms.add(form)

    # if not wikibase_lemma:
    #     print(f"lexeme {lexeme} has only #DEF# in 1.p. present, skipped in this run.")
    #     with open("data/enhanced_forms_skipped_lexemes_lexemes_upload.txt", "a") as logfile:
    #         logfile.write(f"{lexeme}\n")
    #     continue

    with open("test_lexeme_entry.json", "w") as jsonfile:
        json.dump(new_lexeme.get_json(), jsonfile, indent=2)
    # new_lexeme.write()
    # with open("mappings/prinparlat_wikibase_mapping_lexemes.csv", "a") as mappingfile:
    #     mappingfile.write(f"{rowdata['lexeme']}\t{rowdata['lexeme']}\t{rowdata['lila_id_lemma']}\t{new_lexeme.id}\n")
    print(f"Sucessfully created Lexeme https://lilamorph.wikibase.cloud/entity/{new_lexeme.id} and added {rowcount} forms.")
    time.sleep(0.34)
    if rowcount > 500:
        break
sys.exit()
