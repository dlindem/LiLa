import csv, time, sys
import config_private
from wikibaseintegrator import WikibaseIntegrator, wbi_login, datatypes
from wikibaseintegrator.wbi_config import config
config['MEDIAWIKI_API_URL'] = "https://lilamorph.wikibase.cloud/w/api.php"
config['USER_AGENT'] = "upload_prinparlat_lexemes.py"
print("Getting logged into lilamorph wikibase...")
lilamorph = WikibaseIntegrator(login=wbi_login.Login(user=config_private.wbuser, password=config_private.wbpwd))
print("Login successful.")


with open('data/matching_tokens_lexemedict_v2_short.csv') as file:
    rows = csv.DictReader(file, delimiter=",")
    count = 0
    for row in rows:
        count += 1
        if count < 60339:
            continue
        print(f"\nNow processing row [{count}]: {row}")
        entity = lilamorph.item.get(entity_id=row['token_qid'])
        entity.claims.add(datatypes.Form(prop_nr="P21", value=row['matching_form']))
        entity.write()
        print(f"Successfully written claim to {entity.id}")
        time.sleep(.3)

