import csv, time, sys
import config_private
from wikibaseintegrator import WikibaseIntegrator, wbi_login, datatypes
from wikibaseintegrator.wbi_config import config
from wikibaseintegrator.wbi_enums import ActionIfExists
from wikibaseintegrator.models import Qualifiers, References, Reference

config['MEDIAWIKI_API_URL'] = "https://lilamorph.wikibase.cloud/w/api.php"
config['USER_AGENT'] = "upload_prinparlat_lexemes.py"
print("Getting logged into lilamorph wikibase...")
lilamorph = WikibaseIntegrator(login=wbi_login.Login(user=config_private.wbuser, password=config_private.wbpwd))
print("Login successful.")

with open('data/token_form_links_v3.csv') as file:
    rows = csv.DictReader(file, delimiter="\t")
    done_links = {}
    for row in rows:
        if row['token'] not in done_links:
            done_links[row['token']] = [row['linked_form']]
        else:
            done_links[row['token']].append(row['linked_form'])
print(f"Found {len(done_links)} tokens with already written links.")

mapping = ""
with open('data/matching_tokens_lexemedict_variants_v3.csv') as file:
    rows = csv.DictReader(file, delimiter="\t")
    count = 0
    loaded_token = None
    for row in rows:
        count += 1
        print(f"\nNow processing row [{count}]: {row}")

        matching_form = row['matching_form'].replace("https://lilamorph.wikibase.cloud/entity/", "")

        if row['token_qid'] in done_links:
            if matching_form in done_links[row['token_qid']]:
                print(f"Link is already there, no need to write.")
                continue

        if row['token_qid'] != loaded_token:
            entity = lilamorph.item.get(entity_id=row['token_qid'])
        loaded_token = row['token_qid']

        qualifiers = Qualifiers()
        qualifiers.add(datatypes.Item(prop_nr="P14", value="Q15"))
        references = References()
        reference = Reference()
        reference.add(datatypes.URL(prop_nr="P23",
                                    value="https://github.com/dlindem/LiLa/blob/f767253ef52988176011fc6d5ad84651da38243f/match_token_lemmavariant_form.py"))
        references.add(reference)
        entity.claims.add(
            datatypes.Form(prop_nr="P21", value=matching_form, qualifiers=qualifiers, references=references),
            action_if_exists=ActionIfExists.APPEND_OR_REPLACE)
        entity.write()

        print(f"Successfully written claim to https://lilamorph.wikibase.cloud/entity/{entity.id}")
        time.sleep(.34)

        with open('data/token_form_links_v3.csv', 'a') as outfile:
            outfile.write(f"{row['token_qid']}\t{matching_form}\n")
