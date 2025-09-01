import csv, json

tags = {'prs': 'Q192613', 'act': 'Q1317831', 'ind': 'Q682111', '1': 'Q21714344', 'sg': 'Q110786', 'ptcp': 'Q2215850',
        'acc': 'Q146078',
        'n': 'Q1775461', 'pl': 'Q146786', 'sbjv': 'Q473746', 'voc': 'Q185077', 'm': 'Q499327', 'f': 'Q1775415',
        'abl': 'Q156986', '3': 'Q51929074',
        '2': 'Q51929049', 'iprf': 'Q12547192', 'nom': 'Q131105', 'gen': 'Q146233', 'dat': 'Q145599', 'pass': 'Q1194697',
        'imp': 'Q22716',
        'fut': 'Q501405', 'inf': 'Q179230', 'gdv': 'Q731298', 'ger': 'Q1923028', 'pprf': 'Q1823571', 'prf': 'Q625420',
        'fprf': 'Q1234617',
        'sup': 'Q1817208'}

with open("wikidata_tLOkeO.csv") as file:
    csvrows = csv.DictReader(file, delimiter=",")
    wikidata = {}
    for row in csvrows:
        lila_id = row['lila_link'].replace('https://lila-erc.eu/lodview/data/id/lemma/','')
        form_data = {
            'lemma': row['lemma'],
            'form_rep': row['form_rep'],
            'form_uri': row['form'],
            'gramm_feat': row['gramm'].split(' ')
            }
        if lila_id not in wikidata:
            wikidata[lila_id] = [form_data]
        else:
            wikidata[lila_id].append(form_data)

print("Data from Wikidata loaded to memory")

with open("intersection_lilamorph_wikidata.json") as file:
    intersection = json.load(file)

matching_forms_same_gramm = []
matching_forms_different_gramm = []

with open("enhanced_forms.csv") as file:
    csvrows = csv.DictReader(file, delimiter=",")

    for row in csvrows:

        print(row[""])
        if row['lila_id_lemma'] not in intersection:
            continue
        taglist = row["cell"]
        taglisttags = taglist.split(".")
        matching_forms = []
        for wd_form in wikidata[row['lila_id_lemma']]:
            if wd_form['form_rep'] == row['form_normalized']:
                matching_forms.append(wd_form)
            for matching_form in matching_forms:
                wd_tags = matching_form['gramm_feat']
                for tag in taglisttags:
                    if tags[tag] in wd_tags:
                        wd_tags.remove(tags[tag])
                    # else:
                    #     with open('intersection_different_gramm_wd_has_less.jsonl', 'a') as lfile:
                    #         lfile.write(json.dumps({wd_form['form_uri']: row})+'\n')
                    #     continue
                if len(wd_tags) == 0:
                    matching_forms_same_gramm.append({wd_form['form_uri']: row[""]})
                # else:
                #     with open('intersection_different_gramm_wd_has_more.jsonl', 'a') as lfile:
                #         lfile.write(json.dumps({wd_form['form_uri']: row})+'\n')


with open('intersection_same_gramm.json', 'w') as lfile:
    # lfile.write(json.dumps({wd_form['form_uri']: row})+'\n')
    json.dump(matching_forms_same_gramm, lfile, indent=2)