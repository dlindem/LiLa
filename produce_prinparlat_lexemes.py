import csv, sys, time, re, json, requests
import config_private  # bot user and pwd from hidden file

# wikibaseintegrator for lilamorph wikibase
from wikibaseintegrator import WikibaseIntegrator, wbi_login, datatypes
from wikibaseintegrator.models import Reference, References, Form, Sense, Qualifiers
from wikibaseintegrator.wbi_enums import ActionIfExists
from wikibaseintegrator.wbi_config import config

config['MEDIAWIKI_API_URL'] = "https://lilamorph.wikibase.cloud/w/api.php"
config['USER_AGENT'] = "upload_prinparlat_lexemes.py"
print("Getting logged into lilamorph wikibase...")
lilamorph_wbi = WikibaseIntegrator(login=wbi_login.Login(user=config_private.wbuser, password=config_private.wbpwd))
print("Login successful.")

# get prinparlat cell descriptors mapping
with open("mappings/paralex_featurevalue_mapping.csv") as file:
    mappingrows = csv.reader(file, delimiter="\t")
    featurevalue_qid = {}
    for row in mappingrows:
        featurevalue_qid[row[0]] = row[1]
print(f"featurevalue cell descriptors mapping: {featurevalue_qid}")

# get prinparlat cell descriptors mapping
with open("mappings/paralex_cells_wikibase.csv") as file:
    mappingrows = csv.reader(file, delimiter="\t")
    celltypes = {}
    for row in mappingrows:
        celltypes[row[0]] = row[1]
print(f"paralex cells mapping: {celltypes}")

# get prinparlat cell types default order
with open("mappings/celltypes_sorted.txt") as file:
    celltypes_sorted = file.read().split("\n")
cellfeatures = {}
for celltype in celltypes_sorted:
    cellfeatures[celltype] = []
    for val in celltype.split("."):
        cellfeatures[celltype].append(featurevalue_qid[val])
print(f"cellfeatures dict: {cellfeatures}")

# get prinparlat cell types default order
with open("data/prinparlat_lexemes_canonical_forms.csv") as file:
    mappingrows = csv.DictReader(file, delimiter="\t")
    canonicalforms = {}
    for row in mappingrows:
        canonicalforms[row['lexeme_id']] = row['label']
print(f"Loaded canonical forms for {len(canonicalforms)} prinparlat lemma id.")

# read mappingfile (lexemes processed before)
with open("mappings/prinparlat_wikibase_mapping_lexemes_v3.csv", "r") as mappingfile:
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
        writerow = row
        lexeme_id = row['lexeme']
        if "#DEF#" in row['form_normalized']:
            continue
        if row['flexeme'] == "":  # flexeme id cannot be empty
            writerow['flexeme'] = "0"
            print(writerow)
        if lexeme_id not in canonicalforms:
            print(f"Lexeme {lexeme_id} not found in canonical forms list.")
            sys.exit()
        if lexeme_id not in lexemes:
            lexemes[lexeme_id] = {'canonical': canonicalforms[lexeme_id], 'flexemes': [], 'lila_lemmas': {},
                                  'cells': {}}
        if row['flexeme'] not in lexemes[lexeme_id]['flexemes']:
            lexemes[lexeme_id]['flexemes'].append(row['flexeme'])
        if row['lila_id_lemma'] not in lexemes[lexeme_id]['lila_lemmas']:
            lexemes[lexeme_id]['lila_lemmas'][row['lila_id_lemma']] = [row['flexeme']]
        elif row['flexeme'] not in lexemes[lexeme_id]['lila_lemmas'][row['lila_id_lemma']]:
            lexemes[lexeme_id]['lila_lemmas'][row['lila_id_lemma']].append(row['flexeme'])
        if row['cell'] not in lexemes[lexeme_id]['cells']:
            lexemes[lexeme_id]['cells'][row['cell']] = {'rows': [], 'conflations': {}}
        lexemes[lexeme_id]['cells'][row['cell']]['rows'].append(writerow)
        # if len(lexemes[lexeme_id]['lila_lemmas']) > 1:
        #     print(f"*** Lexeme {lexeme_id} is linked to more than one lila lemma: {lexemes[lexeme_id]['lila_lemmas']}")
    print(f"lexemes lexicon built: ({len(lexemes)} lexemes).")

# build form conflations in lexemes
for lexeme_id in lexemes:
    for cell in lexemes[lexeme_id]['cells']:
        cell_amount = len(lexemes[lexeme_id]['cells'][cell]['rows'])
        if cell_amount == 1:  # no conflation possible
            continue
        conflations = {}
        conflated = []
        cellcount = 0
        while cellcount < cell_amount:
            target_row = lexemes[lexeme_id]['cells'][cell]['rows'][cellcount]
            # print(f"target cell: {target_row}")
            if target_row['form_id'] not in conflated:  # if not already part of a conflation
                for source_row in lexemes[lexeme_id]['cells'][cell]['rows']:
                    if source_row['form_id'] != target_row['form_id'] and source_row['analysed_orth_form'] == \
                            target_row['analysed_orth_form']:
                        if target_row['form_id'] not in conflations:
                            conflations[target_row['form_id']] = {target_row['form_id']: target_row['flexeme']}
                            conflated.append(target_row['form_id'])
                        conflations[target_row['form_id']][source_row['form_id']] = source_row['flexeme']
                        conflated.append(source_row['form_id'])
            cellcount += 1
        lexemes[lexeme_id]['cells'][cell]['conflations'] = conflations
print("Conflations dictionary built.")

with open('data/v3_conflation.json', 'w') as jsonfile:
    json.dump(lexemes["a0200"], jsonfile, indent=2)

lexeme_count = 0

for lexeme_id in lexemes:
    lexeme_count += 1
    done_form_id = []
    print(f"\nNow processing lexeme {lexeme_count}/{len(lexemes)}: {lexeme_id}, '{lexemes[lexeme_id]['canonical']}'")
    if lexeme_id in done_lexeme_ids:
        print(f"{lexeme_id} lexeme_id has been done before (found in mappingfile), skipped.")
        continue

    rowcount = 0
    formscount = 0
    new_forms = []

    lexeme_entity = None
    # ask for forms data from the formtypes (celltypes) canonical order list
    for celltype in celltypes_sorted:
        for cell in lexemes[lexeme_id]['cells']:
            if cell != celltype:  # no celltype match
                continue
            celltype_qid = celltypes[celltype]

            for row in lexemes[lexeme_id]['cells'][cell]['rows']:

                rowcount += 1
                if row['form_id'] in done_form_id:
                    continue  # this form has been done before because it is part of a conflation
                if row['form_id'] in lexemes[lexeme_id]['cells'][cell][
                    'conflations']:  # if head of (first row in) conflation
                    conflation_flexemes = lexemes[lexeme_id]['cells'][cell]['conflations'][row['form_id']].values()
                    done_form_id += lexemes[lexeme_id]['cells'][cell]['conflations'][row['form_id']].keys()
                else:  # if not part of a conflation
                    conflation_flexemes = [row['flexeme']]
                    done_form_id.append(row['form_id'])

                # build new form (wikibaseintegrator version)
                form = Form()
                form.representations.set(language='la', value=row['form_normalized'])
                form.grammatical_features = cellfeatures[celltype]
                for flex_id in conflation_flexemes:
                    form.claims.add(datatypes.ExternalID(prop_nr="P6", value=flex_id),
                                    action_if_exists=ActionIfExists.APPEND_OR_REPLACE)
                form.claims.add(datatypes.MonolingualText(prop_nr="P11", language="la", text=row['orth_form']))
                form.claims.add(datatypes.String(prop_nr="P12", value=row['analysed_orth_form']))
                form.claims.add(datatypes.Item(prop_nr="P24", value=celltype_qid))
                new_forms.append(form)

    # with open("test_lexeme_entry.json", "w") as jsonfile:
    #     json.dump(new_lexeme.get_json(), jsonfile, indent=2)
    if len(new_forms) == 0:
        print("Error: no forms to write to this lexeme.")
        sys.exit()

    # make batches of max. 220 forms (batch size will stay below 1 MB)
    write_batches = int(len(new_forms) / 220 + 1)
    print(f"We have {len(new_forms)} to write, in {write_batches} batches.")
    write_batch_num = 0
    while write_batch_num < write_batches:
        # write lexeme forms batch
        batch_done = False
        attempts = 0
        while not batch_done and attempts < 3:
            if not lexeme_entity:
                lexeme_entity = lilamorph_wbi.lexeme.new(language="Q3", lexical_category="Q5")  # latin verb
                lexeme_entity.lemmas.set(language="la", value=lexemes[lexeme_id]['canonical'])  # wikibase lemma
                lexeme_entity.claims.add(datatypes.Item(prop_nr="P14", value="Q15"))  # collection
                qualifiers = Qualifiers()
                for flex_id in lexemes[lexeme_id]['flexemes']:
                    qualifiers.add(datatypes.ExternalID(prop_nr="P6", value=flex_id),
                                   action_if_exists=ActionIfExists.FORCE_APPEND)
                    lexeme_entity.claims.add(datatypes.ExternalID(prop_nr="P8", value=lexeme_id,
                                                                  qualifiers=qualifiers))  # prinparlat lexeme id

                for lila_lemma_id in lexemes[lexeme_id]['lila_lemmas']:
                    qualifiers = Qualifiers()
                    for flex_id in lexemes[lexeme_id]['lila_lemmas'][lila_lemma_id]:
                        qualifiers.add(datatypes.ExternalID(prop_nr="P6", value=flex_id),
                                       action_if_exists=ActionIfExists.FORCE_APPEND)
                    lexeme_entity.claims.add(
                        datatypes.ExternalID(prop_nr="P1", value=f"lemma/{lila_lemma_id}", qualifiers=qualifiers),
                        action_if_exists=ActionIfExists.APPEND_OR_REPLACE)  # lila lemma id

            for f in new_forms[:220]:
                lexeme_entity.forms.add(f)
            print(f"Write batch #{write_batch_num + 1}: Will write {len(new_forms[0:220])} forms to lexeme.")
            attempts += 1
            try:

                lexeme_entity.write()
                write_batch_num += 1
                del new_forms[:220]
                print(
                    f"Sucessfully written to Lexeme https://lilamorph.wikibase.cloud/entity/{lexeme_entity.id}; {len(new_forms)} forms left.")
                if write_batch_num > 0 and len(new_forms) > 0:
                    lastrevid = lexeme_entity.lastrevid
                    json_lexeme = lexeme_entity.get_json()
                    json_lexeme['forms'] = []
                    json_lexeme['lastrevid'] = lastrevid  # lastrevid seems to get lost after get_JSON conversion
                    lexeme_entity = lilamorph_wbi.lexeme.from_json(json_lexeme)
                    print("Lexeme forms reset, will write more forms.")
                    time.sleep(.51)
                batch_done = True
            except Exception as ex:
                errortext = str(ex)
                if "The entity is too big. The maximum allowed entity size is 2 MB." in errortext:  # too large (reaches 2 MB)
                    print(
                        "\nLexeme is too big for normal strategy (lexeme JSON data will exceed 2MB). Will have to set up another wikibase lexeme entity...")
                    with open("mappings/prinparlat_wikibase_mapping_lexemes_v3.csv", "a") as mappingfile:
                        mappingfile.write(f"{lexeme_id}\t{lexeme_entity.id}\t{json.dumps(done_form_id)}\n")
                    lexeme_entity = None  # leads to the creation of a new one
                    time.sleep(1)
        if not batch_done:
            print(errortext)
            with open('data/failed_lexemes_v3.txt', 'a') as errorlog:
                errorlog.write(f'{lexeme_id}\t{lexeme_entity.id}\t{errortext}\n')
            sys.exit()

    with open("mappings/prinparlat_wikibase_mapping_lexemes_v3.csv", "a") as mappingfile:
        mappingfile.write(f"{lexeme_id}\t{lexeme_entity.id}\t{json.dumps(done_form_id)}\n")
    time.sleep(.51)

print("\nFinished.")
sys.exit()
