import csv, sys, time, re, json, requests
import config_private # bot user and pwd from hidden file

# import mwclient # mediawiki api client (will be used for itemdata > 1MB
# lilamorph_api = mwclient.Site('lilamorph.wikibase.cloud')
# login = lilamorph_api.login(username=config_private.wbuser, password=config_private.wbpwd)
# csrfquery = lilamorph_api.api('query', meta='tokens')
# lilamorph_api_token = csrfquery['query']['tokens']['csrftoken']
# print("Got fresh CSRF token for lilamorph.wikibase.cloud.")
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
            with open("mappings/prinparlat_wikibase_mapping_lexemes_v2c.csv", "a") as mappingfile:
                mappingfile.write(f"{lexeme_id}\t{new_lexeme.id}\n")
            print(
                f"Sucessfully written to Lexeme https://lilamorph.wikibase.cloud/entity/{new_lexeme.id}.")
            return new_lexeme.id
        except Exception as ex:
            print(str(ex))
            errortext = str(ex).replace("\n", " ")
            with open('data/failed_lexemes_v2c.txt', 'a') as errorlog:
                errorlog.write(f'{lexeme_id}\t{rowcount}\t{errortext}\n')
        return False

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

# read mappingfile (lexemes processed before)
with open("mappings/prinparlat_wikibase_mapping_lexemes_v2c.csv", "r") as mappingfile:
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
            if f"{target_row['flexeme']}@{target_row['analysed_orth_form']}" not in conflated: # if not already part of a conflation
                for source_row in lexemes[lexeme_id]['cells'][cell]['rows']:
                    if source_row['flexeme'] != target_row['flexeme'] and source_row['orth_form'] == target_row['orth_form'] and source_row['analysed_orth_form'] == target_row['analysed_orth_form']:
                        if f"{target_row['analysed_orth_form']}" not in conflations:
                            conflations[f"{target_row['analysed_orth_form']}"] = [target_row['flexeme']]
                        conflations[f"{target_row['analysed_orth_form']}"].append(source_row['flexeme'])
                        conflated.append(f"{source_row['flexeme']}@{source_row['analysed_orth_form']}") # unique combination of flex_id, orth_form and analyzed_orth_form
            cellcount += 1
        lexemes[lexeme_id]['cells'][cell]['conflations'] = conflations
print("Conflations dictionary built.")

with open('data/v2_conflation.json', 'w') as jsonfile:
    json.dump(lexemes["a0200"], jsonfile, indent=2)



lexeme_count = 0

for lexeme_id in lexemes:
    lexeme_count += 1

    print(f"\nNow processing lexeme {lexeme_count}/{len(lexemes)}: {lexeme_id}, '{lexemes[lexeme_id]['canonical']}'")
    if lexeme_id in done_lexeme_ids:
        print(f"{lexeme_id} lexeme_id has been done before (found in mappingfile), skipped.")
        continue

    rowcount = 0
    formscount = 0
    new_forms = []
    queryurl = f"https://lilamorph.wikibase.cloud/query/sparql?format=json&query=PREFIX%20lmwb%3A%20%3Chttps%3A%2F%2Flilamorph.wikibase.cloud%2Fentity%2F%3E%0APREFIX%20lmdp%3A%20%3Chttps%3A%2F%2Flilamorph.wikibase.cloud%2Fprop%2Fdirect%2F%3E%0A%0A%20select%20%0A%20%20%3Flexeme%20%3Fprinparlat_lexeme%20%3Fcell%20%3Fform%20%3Fform_rep%20%3Fanalyzed_orth_form%20(group_concat(%3Fflexeme)%20as%20%3Fflexemes)%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%0A%20%20%20%20%20where%20%7B%20%20%20%20values%20%3Fprinparlat_lexeme%20%7B%22{lexeme_id}%22%7D%0A%20%20%3Flexeme%20lmdp%3AP14%20lmwb%3AQ14%3B%20lmdp%3AP8%20%3Fprinparlat_lexeme.%0A%20%20%3Flexeme%20ontolex%3AlexicalForm%20%3Fform.%0A%20%20%3Fform%20lmdp%3AP6%20%3Fflexeme%3B%20ontolex%3Arepresentation%20%3Fform_rep%3B%20lmdp%3AP13%20%3Fcell%3B%20lmdp%3AP12%20%3Fanalyzed_orth_form.%0A%20%20%7D%20group%20by%20%3Flexeme%20%3Fprinparlat_lexeme%20%3Fcell%20%3Fform%20%3Fform_rep%20%3Fanalyzed_orth_form%20%3Fflexemes%20"
    wblexemedata = requests.get(queryurl).json()['results']['bindings']
    print(f"Got {len(wblexemedata)} rows of formdata for {lexeme_id}")
    wblexeme_id = wblexemedata[0]['lexeme']['value'].replace("https://lilamorph.wikibase.cloud/entity/","")
    # ask for forms data from the formtypes (celltypes) canonical order list
    for celltype in celltypes_sorted:
        for cell in lexemes[lexeme_id]['cells']:
            if cell != celltype: # no celltype match
                continue
            done_forms = []
            for row in lexemes[lexeme_id]['cells'][cell]['rows']:

                rowcount += 1
                if row['analysed_orth_form'] in done_forms:
                    continue
                if row['analysed_orth_form'] in lexemes[lexeme_id]['cells'][cell]['conflations']:
                    cell_flex_ids = lexemes[lexeme_id]['cells'][cell]['conflations'][row['analysed_orth_form']]
                else:
                    cell_flex_ids = [row['flexeme']]
                done_forms.append(row['analysed_orth_form'])


                # Check form
                row_is_there = False
                for wbform in wblexemedata:
                    if wbform['cell']['value'] == celltype:
                        if wbform['form_rep']['value'] == row['form_normalized'] and wbform['analyzed_orth_form']['value'] == row['analysed_orth_form']:
                            if row['flexeme'] not in wbform['flexemes']['value'].split(" "):
                                print(f"found BIG PROBLEM in row (flexeme id not listed in formrep group) {row}")
                                sys.exit()
                            else:
                                # print(f"found row {row} in Wikibase.")
                                row_is_there = True
                                break
                if row_is_there:
                    continue


                # build new form
                form = Form()
                form.representations.set(language='la', value=row['form_normalized'])
                form.grammatical_features = cellfeatures[celltype]
                for flex_id in cell_flex_ids:
                    form.claims.add(datatypes.ExternalID(prop_nr="P6", value=flex_id), action_if_exists=ActionIfExists.APPEND_OR_REPLACE)
                form.claims.add(datatypes.MonolingualText(prop_nr="P11", language="la", text=row['orth_form']))
                form.claims.add(datatypes.String(prop_nr="P12", value=row['analysed_orth_form']))
                form.claims.add(datatypes.String(prop_nr="P13", value=celltype))
                new_forms.append(form)


    # with open("test_lexeme_entry.json", "w") as jsonfile:
    #     json.dump(new_lexeme.get_json(), jsonfile, indent=2)
    if len(new_forms) > 0:
        json_lexeme = \
        requests.get(f"https://lilamorph.wikibase.cloud/wiki/Special:EntityData/{wblexeme_id}.json").json()['entities'][
            wblexeme_id]
        json_lexeme['forms'] = []

        if len(new_forms) > 250:
            lexeme_entity = lilamorph.lexeme.from_json(json_lexeme)
            for f in new_forms[:250]:
                lexeme_entity.forms.add(f)
            print(f"Will write {len(new_forms[:250])} forms to lexeme.")
            lexeme_entity_id = write_lexeme(lexeme_entity)
            if lexeme_entity_id:
                print(f"First write operation to {lexeme_entity_id} successful, with {len(wblexemedata)+len(new_forms[:250])} forms.")
                del new_forms [:250]
                time.sleep(2)
            else:
                print(f"*** Failed writing.")
                continue

        lexeme_entity = lilamorph.lexeme.from_json(json_lexeme)
        for f in new_forms:
            lexeme_entity.forms.add(f)
        print(f"Will write {len(new_forms)} forms to lexeme.")
        lexeme_entity_id = write_lexeme(lexeme_entity)
        if lexeme_entity_id:
            print(
                f"Write operation to {lexeme_entity_id} successful, with {len(wblexemedata) + len(new_forms)} forms.")
        else:
            print(f"*** Failed writing.")
    else:
        with open("mappings/prinparlat_wikibase_mapping_lexemes_v2c.csv", "a") as mappingfile:
            mappingfile.write(f"{lexeme_id}\t{wblexeme_id}\n")
        print("No change necessary for this lexeme.")
    time.sleep(1)



print("\nFinished.")
sys.exit()
