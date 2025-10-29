import csv, sys, time, re, json, requests
import config_private # bot user and pwd from hidden file

import mwclient # mediawiki api client (will be used for itemdata > 1MB
lilamorph_api = mwclient.Site('lilamorph.wikibase.cloud')
login = lilamorph_api.login(username=config_private.wbuser, password=config_private.wbpwd)
csrfquery = lilamorph_api.api('query', meta='tokens')
lilamorph_api_token = csrfquery['query']['tokens']['csrftoken']
print("Got fresh CSRF token for lilamorph.wikibase.cloud.")
# wikibaseintegrator for lilamorph wikibase
from wikibaseintegrator import WikibaseIntegrator, wbi_login, datatypes
from wikibaseintegrator.models import Reference, References, Form, Sense
from wikibaseintegrator.wbi_enums import ActionIfExists
from wikibaseintegrator.wbi_config import config
config['MEDIAWIKI_API_URL'] = "https://lilamorph.wikibase.cloud/w/api.php"
config['USER_AGENT'] = "upload_prinparlat_lexemes.py"
print("Getting logged into lilamorph wikibase...")
lilamorph = WikibaseIntegrator(login=wbi_login.Login(user=config_private.wbuser, password=config_private.wbpwd))
print("Login successful.")

def write_lexeme(new_lexeme):
    done = False
    attempts = 0
    while not done and attempts < 3:
        attempts += 1
        try:
            new_lexeme.write()
            done = True
            with open("mappings/prinparlat_wikibase_mapping_lexemes_v2.csv", "a") as mappingfile:
                mappingfile.write(f"{lexeme_id}\t{lila_lemma_id}\t{new_lexeme.id}\n")
            print(
                f"Sucessfully created Lexeme https://lilamorph.wikibase.cloud/entity/{new_lexeme.id} and added {rowcount} forms.")
            return new_lexeme.id
        except Exception as ex:
            print(str(ex))
            errortext = str(ex).replace("\n", " ")
            with open('data/failed_lexemes_v2.txt', 'a') as errorlog:
                errorlog.write(f'{lexeme_id}\t{rowcount}\t{errortext}\n')
        return False

# get prinparlat cell descriptors mapping
with open("mappings/paralex_featurevalue_mapping.csv") as file:
    mappingrows = csv.reader(file, delimiter="\t")
    leipzig_qid = {}
    for row in mappingrows:
        leipzig_qid[row[0]] = row[1]
print(f"Leipzig cell descriptors mapping: {leipzig_qid}")

# get prinparlat cell types default order
with open("mappings/celltypes_sorted.txt") as file:
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
with open("mappings/prinparlat_wikibase_mapping_lexemes_v2.csv", "r") as mappingfile:
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
        if "#DEF#" in row['form_normalized']:
            continue
        if row['flexeme'] == "": # flexeme id cannot be empty
            row['flexeme'] = "0"
            print(row)
        if lexeme_id not in canonicalforms:
            print(f"Lexeme {lexeme_id} not found in canonical forms list.")
            sys.exit()
        if lexeme_id not in lexemes:
            lexemes[lexeme_id] = {'canonical': canonicalforms[lexeme_id], 'cells': {}}
        if row['cell'] not in lexemes[lexeme_id]['cells']:
            lexemes[lexeme_id]['cells'][row['cell']] = {'rows': [], 'conflations': {}}
        lexemes[lexeme_id]['cells'][row['cell']]['rows'].append(row)
    print(f"lexemes lexicon built: ({len(lexemes)} lexemes).")

# build form conflations in lexemes
for lexeme_id in lexemes:
    for cell in lexemes[lexeme_id]['cells']:
        cell_amount = len(lexemes[lexeme_id]['cells'][cell]['rows'])
        if cell_amount == 1:
            continue
        conflations = {}
        conflated = []
        cellcount = 0
        while cellcount < cell_amount:
            target_row = lexemes[lexeme_id]['cells'][cell]['rows'][cellcount]
            # print(f"target cell: {target_row}")
            if target_row['flexeme'] not in conflated: # if not already part of a conflation
                for source_row in lexemes[lexeme_id]['cells'][cell]['rows']:
                    if source_row['flexeme'] != target_row['flexeme'] and source_row['orth_form'] == target_row['orth_form'] and source_row['analysed_orth_form'] == target_row['analysed_orth_form']:
                        if target_row['flexeme'] not in conflations:
                            conflations[target_row['flexeme']] = []
                        conflations[target_row['flexeme']].append(source_row['flexeme'])
                        conflated.append(source_row['flexeme'])
            cellcount += 1
        lexemes[lexeme_id]['cells'][cell]['conflations'] = conflations
print("Conflations dictionary built.")

# with open('data/v2_conflation.json', 'w') as jsonfile:
#     json.dump(lexemes, jsonfile, indent=2)



lexeme_count = 0

for lexeme_id in lexemes:
    lexeme_count += 1
    print(f"\nNow processing lexeme {lexeme_count}/{len(lexemes)}: {lexeme_id}, '{lexemes[lexeme_id]['canonical']}'")
    if lexeme_id in done_lexeme_ids:
        print(f"{lexeme_id} lexeme_id has been done before (found in mappingfile), skipped.")
        continue

    rowcount = 0
    formscount = 0

    new_lexeme = None

    # ask for forms data from the formtypes (celltypes) canonical order list
    for celltype in celltypes_sorted:
        done_flexeme_ids = []
        for cell in lexemes[lexeme_id]['cells']:
            if cell != celltype: # no celltype match
                continue
            for row in lexemes[lexeme_id]['cells'][cell]['rows']:
                if row['flexeme'] in done_flexeme_ids:
                    continue
                rowcount += 1
                formscount += 1

                if not new_lexeme:
                    new_lexeme = lilamorph.lexeme.new(language="Q3", lexical_category="Q5")  # latin verb
                    new_lexeme.lemmas.set(language="la", value=lexemes[lexeme_id]['canonical']) # wikibase lemma
                    new_lexeme.claims.add(datatypes.Item(prop_nr="P14", value="Q14")) # collection
                    new_lexeme.claims.add(datatypes.ExternalID(prop_nr="P8", value=lexeme_id)) # prinparlat lexeme id
                    lila_lemma_id = lexemes[lexeme_id]['cells'][cell]['rows'][0]['lila_id_lemma']
                    new_lexeme.claims.add(datatypes.ExternalID(prop_nr="P1", value=f"lemma/{lila_lemma_id}")) # lila lemma id

                if row['flexeme'] in lexemes[lexeme_id]['cells'][cell]['conflations']:
                    cell_flex_ids = [row['flexeme']] + lexemes[lexeme_id]['cells'][cell]['conflations'][row['flexeme']]
                else:
                    cell_flex_ids = [row['flexeme']]
                done_flexeme_ids += cell_flex_ids

                # Create form (normal mode)
                form = Form()
                form.representations.set(language='la', value=row['form_normalized'])
                form.grammatical_features = cellfeatures[celltype]
                for flex_id in cell_flex_ids:
                    form.claims.add(datatypes.ExternalID(prop_nr="P6", value=flex_id), action_if_exists=ActionIfExists.APPEND_OR_REPLACE)
                form.claims.add(datatypes.MonolingualText(prop_nr="P11", language="la", text=row['orth_form']))
                form.claims.add(datatypes.String(prop_nr="P12", value=row['analysed_orth_form']))
                form.claims.add(datatypes.String(prop_nr="P13", value=celltype))
                new_lexeme.forms.add(form)

        if rowcount > 400:
            print(f"*** Long lexeme. Will write {rowcount} forms and then proceed ***")
            lexeme_entity_id = write_lexeme(new_lexeme)
            if lexeme_entity_id:
                print(f"*** Written {rowcount} forms to http://lilamorph.wikibase.cloud/entity/{new_lexeme.id}")
            else:
                print(f"Failed writing.")
                break
            time.sleep(2.5)
            json_lexeme = requests.get(f"https://lilamorph.wikibase.cloud/wiki/Special:EntityData/{lexeme_entity_id}.json").json()['entities'][lexeme_entity_id]
            json_lexeme['forms'] = []
            new_lexeme = lilamorph.lexeme.from_json(json_lexeme)
            print(f"*** Set forms to zero in {lexeme_entity_id} after writing {rowcount} forms ***")
            rowcount = 0
    # with open("test_lexeme_entry.json", "w") as jsonfile:
    #     json.dump(new_lexeme.get_json(), jsonfile, indent=2)

    print(f"Will write {rowcount} forms to lexeme.")
    lexeme_entity_id = write_lexeme(new_lexeme)
    if lexeme_entity_id:
        print(f"Finished {lexeme_entity_id}, with {formscount} forms.")
    else:
        print(f"*** Failed writing.")
    time.sleep(2.5)


print("\nFinished.")
sys.exit()
