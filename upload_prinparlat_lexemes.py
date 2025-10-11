import csv, sys, time, re, json

# wikibaseintegrator for lilamorph wikibase
from wikibaseintegrator import WikibaseIntegrator, wbi_login, datatypes
from wikibaseintegrator.models import Reference, References, Form, Sense
from wikibaseintegrator.wbi_config import config
import config_private # bot user and pwd from hidden file
config['MEDIAWIKI_API_URL'] = "https://lilamorph.wikibase.cloud/w/api.php"
config['USER_AGENT'] = "upload_prinparlat_lexemes.py"
print("Getting logged into lilamorph wikibase...")
lilamorph = WikibaseIntegrator(login=wbi_login.Login(user=config_private.wbuser, password=config_private.wbpwd))
print("Login successful.")
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

lexeme_count = 0
too_large_lexemes = []
for lexeme_id in lexemes:
    lexeme_count += 1
    print(f"\nNow processing lexeme {lexeme_count}/{len(lexemes)}: {lexeme_id}, '{lexemes[lexeme_id]['canonical']}'")
    if lexeme_id in done_lexeme_ids:
        print(f"{lexeme_id} lexeme_id has been done before (found in mappingfile), skipped.")
        continue

    rowcount = 0
    formnumbercount = 0
    new_lexeme = None

    # ask for forms data from the formtypes (celltypes) canonical order list
    for celltype in celltypes_sorted:
        for flexeme_cell in lexemes[lexeme_id]['data']:
            flexeme_cell_code = flexeme_cell.split("@")
            cell = flexeme_cell_code[1]
            if cell != celltype: # no celltype match
                continue
            rowcount += 1
            flexeme_id = flexeme_cell_code[0]
            rowdata = lexemes[lexeme_id]['data'][flexeme_cell]
            if not new_lexeme:
                new_lexeme = lilamorph.lexeme.new(language="Q3", lexical_category="Q5")  # latin verb
                new_lexeme.lemmas.set(language="la", value=lexemes[lexeme_id]['canonical'])
                new_lexeme.claims.add(datatypes.Item(prop_nr="P14", value="Q10"))
                new_lexeme.claims.add(datatypes.ExternalID(prop_nr="P8", value=lexeme_id))
                new_lexeme.claims.add(datatypes.ExternalID(prop_nr="P1", value=f"lemma/{rowdata['lila_id_lemma']}"))
            if rowdata['form_normalized'] == "#DEF#":  # do not write rows with that to Wikibase
                continue

            # Create form
            formnumbercount += 1
            form = Form()
            form.representations.set(language='la', value=rowdata['form_normalized'])
            form.grammatical_features = cellfeatures[celltype]
            form.claims.add(datatypes.ExternalID(prop_nr="P6", value=flexeme_id))
            form.claims.add(datatypes.MonolingualText(prop_nr="11", language="la", text=rowdata['orth_form']))
            form.claims.add(datatypes.String(prop_nr="12", value=rowdata['analysed_orth_form']))
            form.claims.add(datatypes.String(prop_nr="13", value=celltype))
            new_lexeme.forms.add(form)

        if rowcount > 600:
            print("*** Long lexeme. Will skip this lexeme. ***")
            new_lexeme = None
            break
            # print("*** Long lexeme. Will write 500 forms and then proceed ***")
            # new_lexeme.write()
            # time.sleep(3)
            # lid = new_lexeme.id
            # new_lexeme = lilamorph.lexeme.get(entity_id=lid)
            # rowcount = 0
            # print(f"*** Re-start with lexeme {lid} after writing 500 forms ***")
    # with open("test_lexeme_entry.json", "w") as jsonfile:
    #     json.dump(new_lexeme.get_json(), jsonfile, indent=2)
    done = False
    attempts = 0

    while new_lexeme and not done and attempts < 2:
        attempts += 1
        try:
            new_lexeme.write()
            done = True
            with open("mappings/prinparlat_wikibase_mapping_lexemes.csv", "a") as mappingfile:
                mappingfile.write(f"{rowdata['lexeme']}\t{rowdata['lila_id_lemma']}\t{new_lexeme.id}\n")
            print(f"Sucessfully created Lexeme https://lilamorph.wikibase.cloud/entity/{new_lexeme.id} and added {formnumbercount} forms.")
        except Exception as ex:
            print(str(ex))
            if "Request Entity Too Large" in str(ex) and lexeme_id not in too_large_lexemes:
                with open('data/too_large_lexemes.txt', 'a') as errorlog:
                    errorlog.write(f"{lexeme_id}\t{rowcount}\n")
                    too_large_lexemes.append(lexeme_id)
        time.sleep(1.5)

print("\nFinished.")
sys.exit()
