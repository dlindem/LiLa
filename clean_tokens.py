# removes old token-to-form links (from version 2) from tokens

import requests, re, time
import config_private
import mwclient # mediawiki api client (will be used for itemdata > 1MB
lilamorph_api = mwclient.Site('lilamorph.wikibase.cloud')
login = lilamorph_api.login(username=config_private.wbuser, password=config_private.wbpwd)
csrfquery = lilamorph_api.api('query', meta='tokens')

done_tokens = []
remaining_statements = 1
while remaining_statements > 0:
    lilamorph_api_token = csrfquery['query']['tokens']['csrftoken']
    print("Got fresh CSRF token for lilamorph.wikibase.cloud.")
    # get batch of 2,500 old P21 link statements
    r = requests.get("https://lilamorph.wikibase.cloud/query/sparql?format=json&query=%23title%3A%20Old%20token-to-form%20links%20to%20remove%0APREFIX%20lmwb%3A%20%3Chttps%3A%2F%2Flilamorph.wikibase.cloud%2Fentity%2F%3E%0APREFIX%20lmdp%3A%20%3Chttps%3A%2F%2Flilamorph.wikibase.cloud%2Fprop%2Fdirect%2F%3E%0APREFIX%20lmp%3A%20%3Chttps%3A%2F%2Flilamorph.wikibase.cloud%2Fprop%2F%3E%0APREFIX%20lmps%3A%20%3Chttps%3A%2F%2Flilamorph.wikibase.cloud%2Fprop%2Fstatement%2F%3E%0APREFIX%20lmpq%3A%20%3Chttps%3A%2F%2Flilamorph.wikibase.cloud%2Fprop%2Fqualifier%2F%3E%0A%0Aselect%20distinct%20%3Ftoken%20%3Fp21_st%0A%20%0A%0Awhere%20%7B%20%0A%20%20%3Ftoken%20lmdp%3AP14%20lmwb%3AQ13.%20%23%20in%20collection%20ITTB%0A%20%20%3Ftoken%20lmp%3AP21%20%3Fp21_st.%20%0A%20%20%20%20%20%20%20filter%20not%20exists%20%7B%3Fp21_st%20lmpq%3AP14%20%3Fcollection.%7D%0A%20%20%0A%7D%20limit%202500")
    bindings = r.json()['results']['bindings']
    remaining_statements = len(bindings)
    count = 0
    for binding in bindings:
        count += 1
        guid = binding['p21_st']['value'].replace("https://lilamorph.wikibase.cloud/entity/statement/","")
        guidfix = re.compile(r'^(Q\d+)\-')
        guid = re.sub(guidfix, r'\1$', guid)
        if guid in done_tokens:
            print("Done before (no time for sparql to update...)")
            continue

        try:
            results = lilamorph_api.post('wbremoveclaims', claim=guid, token=lilamorph_api_token)
            if results['success'] == 1:
                print(f'Wb remove claim for {binding["token"]["value"]} success. {remaining_statements - count} left in this batch.')
                done_tokens.append(guid)
        except Exception as ex:
                print(str(ex))
        time.sleep(.34)

    print("Ended batch, sleep and get more...")
    sec = 120
    while sec > 0:
        print(f"{sec} sec left")
        sec = sec - 10
        time.sleep(10)
    print("\nSPARQL by now should have updated.")

print("Finished.")