import csv, time, sys
import config_private
from wikibaseintegrator import WikibaseIntegrator, wbi_login, datatypes
from wikibaseintegrator.wbi_config import config
from wikibaseintegrator.wbi_enums import ActionIfExists
config['MEDIAWIKI_API_URL'] = "https://lilamorph.wikibase.cloud/w/api.php"
config['USER_AGENT'] = "upload_prinparlat_lexemes.py"
print("Getting logged into lilamorph wikibase...")
lilamorph = WikibaseIntegrator(login=wbi_login.Login(user=config_private.wbuser, password=config_private.wbpwd))
print("Login successful.")

with open('data/token-form-links-2f.csv') as file:
    rows = csv.DictReader(file, delimiter=",")
    done_links = {}
    for row in rows:
        if row['token'] not in done_links:
            done_links[row['token']] = [row['linked_form']]
        else:
            done_links[row['token']].append(row['linked_form'])


# mapping = ""
with open('data/matching_tokens_lexemedict_v2f.csv') as file:
    rows = csv.DictReader(file, delimiter="\t")
    count = 0
    for row in rows:
        count += 1

        matching_form = row['matching_form'].replace("https://lilamorph.wikibase.cloud/entity/", "")
        if row['token_qid'] in done_links:
            if matching_form in done_links[row['token_qid']]:
                # print(f"Link is already there, no need to write.")
                continue
        # mapping += f"{row['token_qid']}\tP21\t{matching_form}\n"
        entity = lilamorph.item.get(entity_id=row['token_qid'])
        entity.claims.add(datatypes.Form(prop_nr="P21", value=matching_form), action_if_exists=ActionIfExists.FORCE_APPEND)
        entity.write()
        print(f"\nNow processing row [{count}]: {row}")
        print(f"Successfully written claim to {entity.id}")
        time.sleep(1)

# with open('data/p21e.csv', 'w') as file:
#     file.write(mapping)

