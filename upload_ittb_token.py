import csv, time, sys

# wikibaseintegrator for lilamorph wikibase
from wikibaseintegrator import WikibaseIntegrator, wbi_login, datatypes
from wikibaseintegrator.models import Reference, References, Form, Sense
from wikibaseintegrator.wbi_config import config
from wikibaseintegrator.wbi_enums import ActionIfExists
import config_private # bot user and pwd from hidden file
config['MEDIAWIKI_API_URL'] = "https://lilamorph.wikibase.cloud/w/api.php"
config['USER_AGENT'] = "upload_ittb_token.py"
print("Getting logged into lilamorph wikibase...")
lilamorph = WikibaseIntegrator(login=wbi_login.Login(user=config_private.wbuser, password=config_private.wbpwd))
print("Login successful.")

with open('mappings/udp_features_wikibase.csv') as file:
    udp = {}
    udprows = csv.DictReader(file, delimiter="\t")
    for row in udprows:
        udp[row['udp']] = row['qid']

with open('mappings/ITTB_tokens_wikibase.csv') as logfile:
    done_items = {}
    done_rows = csv.DictReader(logfile, delimiter="\t")
    for row in done_rows:
        done_items[row['token_id']] = row['wikibase_qid']

with (open('data/ITTB_verb_tokendata_for_upload.csv') as file):
    ittbrows = csv.DictReader(file, delimiter="\t")
    count = 0
    for row in ittbrows:
        count += 1
        print(f"\n[{count}] Now processing {row}")
        if row['P17'] in done_items:
            if len(row['lila_lemmas'].split("|")) < 2:
                print(f"Token {row['token']} has been done in a previous run, will load.")
            else:
                print(f"Token {row['token']} has been done in a previous run but will be re-written.")
                new_item = lilamorph.item.get(entity_id=done_items[row['token']])
        else:
            new_item = lilamorph.item.new()
        new_item.labels.set(language="la", value=row['tokenLabel'])
        new_item.labels.set(language="en", value=row['tokenLabel'])
        new_item.descriptions.set(language="en", value=f"ITTB token {row['token']}")
        new_item.claims.add(datatypes.Item(prop_nr="P5", value="Q12"), action_if_exists=ActionIfExists.APPEND_OR_REPLACE) # instance of corpus token
        new_item.claims.add(datatypes.Item(prop_nr="P14", value="Q13"), action_if_exists=ActionIfExists.APPEND_OR_REPLACE) # part of ITTB
        token_references = References()
        sourceref = Reference()
        sourceref.add(datatypes.ExternalID(prop_nr="P17", value=row['token'])) # ITTB token ID
        sourceref.add(datatypes.Time(prop_nr="P19", time="now"))
        token_references.add(sourceref)
        anno_references = References()
        sourceref = Reference()
        sourceref.add(datatypes.ExternalID(prop_nr="P20", value=row['token']))  # ITTB token ID
        sourceref.add(datatypes.Time(prop_nr="P19", time="now"))
        anno_references.add(sourceref)
        new_item.claims.add(datatypes.ExternalID(prop_nr="P17", value=row['token'])) # ITTB token ID
        for lila_lemma_id in row['lila_lemmas'].split("|"):
            new_item.claims.add(datatypes.ExternalID(prop_nr="P16", value=lila_lemma_id, references=token_references), action_if_exists=ActionIfExists.APPEND_OR_REPLACE) # linked to Lila Lemma
        for feat in row['features'].split("|"):
            print(f"Adding morph annotation {udp[feat]}")
            new_item.claims.add(datatypes.Item(prop_nr="P18", value=udp[feat], references=anno_references), action_if_exists=ActionIfExists.APPEND_OR_REPLACE)
        done = False
        attempts = 0
        while not done:
            attempts += 1
            try:
                new_item.write()
                done = True
                with open('mappings/ITTB_tokens_wikibase.csv', 'a') as logfile:
                    logfile.write(f"{row['P17']}\t{new_item.id}\n")
                print(f"Successfully written to https://lilamorph.wikibase.cloud/entity/{new_item.id}")
            except Exception as ex:
                print(str(ex))
            time.sleep(3)
            if attempts == 3:
                sys.exit()



print("Finished.")
