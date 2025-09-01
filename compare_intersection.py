import csv, json, sys

tags = {'prs': 'Q192613', 'act': 'Q1317831', 'ind': 'Q682111', '1': 'Q21714344', 'sg': 'Q110786', 'ptcp': 'Q814722',
        'acc': 'Q146078',
        'n': 'Q1775461', 'pl': 'Q146786', 'sbjv': 'Q473746', 'voc': 'Q185077', 'm': 'Q499327', 'f': 'Q1775415',
        'abl': 'Q156986', '3': 'Q51929074',
        '2': 'Q51929049', 'iprf': 'Q12547192', 'nom': 'Q131105', 'gen': 'Q146233', 'dat': 'Q145599', 'pass': 'Q1194697',
        'imp': 'Q22716',
        'fut': 'Q501405', 'inf': 'Q179230', 'gdv': 'Q731298', 'ger': 'Q1923028', 'pprf': 'Q623742', 'prf': 'Q625420',
        'fprf': 'Q1234617',
        'sup': 'Q1817208'}

# with open("wikidata_tLOkeO.csv") as file:
#     csvrows = csv.DictReader(file, delimiter=",")
#     wikidata = {}
#     for row in csvrows:
#         lila_id = row['lila_link'].replace('https://lila-erc.eu/lodview/data/id/lemma/','')
#         form_data = {
#             'lemma': row['lemma'],
#             'form_rep': row['form_rep'],
#             'form_uri': row['form'],
#             'gramm_feat': row['gramm'].split(' ')
#             }
#         if lila_id not in wikidata:
#             wikidata[lila_id] = [form_data]
#         else:
#             wikidata[lila_id].append(form_data)
#
# with open("wikidata_forms.json", "w") as file:
#     json.dump(wikidata, file, indent=2)

with open("wikidata_forms.json") as file:
    wikidata = json.load(file)

with open("intersection_lilamorph_wikidata.json") as file:
    intersection = json.load(file)

matching_forms_output = []
formreps_missing_on_wikidata = []

with open("enhanced_forms.csv") as file:
    csvrows = csv.DictReader(file, delimiter=",")
    for row in csvrows:
        # if int(row[""]) > 5266:
        #     break
        print("\n"+row[""]+" "+row['form_normalized'], end=" ")
        if row['lila_id_lemma'] not in intersection:
            print(" This lemma is not on wikidata", end="")
            continue

        matching_forms = []
        for wd_form in wikidata[row['lila_id_lemma']]:
            if wd_form['form_rep'] == row['form_normalized']:
                matching_forms.append(wd_form)

        if len(matching_forms) == 0:
            formreps_missing_on_wikidata.append({"lila_row": row[""], "lila-lemma": row['lila_id_lemma'], "form_rep": row['form_normalized'], "lila_tags": row["cell"]})

        for matching_form in matching_forms:
            # print(matching_form)
            wd_tags = matching_form['gramm_feat']
            wd_tags_lilaset = []
            for wd_tag in wd_tags:
                for tag in tags:
                    if tags[tag] == wd_tag:
                        wd_tags_lilaset.append(tag)
            found_wd_tags = []
            lila_tags = row["cell"].split(".")

            print(matching_form['form_uri'], end=" ")
            print(len(wd_tags), end=" ")
            remaining_lila_tags = []
            remaining_wd_tags = []
            for lila_tag in lila_tags:
                if lila_tag in wd_tags_lilaset:
                    found_wd_tags.append(lila_tag)
                    # else:
                    #     with open('intersection_different_gramm_wd_has_less.jsonl', 'a') as lfile:
                    #         lfile.write(json.dumps({wd_form['form_uri']: row})+'\n')
                    #     continue
                else:
                    remaining_lila_tags.append(lila_tag)
            for wd_tag_lila in wd_tags_lilaset:
                if wd_tag_lila not in found_wd_tags:
                    remaining_wd_tags.append(wd_tag_lila)
            matching_forms_output.append({matching_form['form_uri']: {"lila_row": row[""], "form_rep": row['form_normalized'], "lila_tags": lila_tags, "wd_tags": wd_tags_lilaset, "wd_not_lila": remaining_wd_tags, "lila_not_wd": remaining_lila_tags}, "deviation": len(remaining_lila_tags)+len(remaining_wd_tags)})


                # else:
                #     with open('intersection_different_gramm_wd_has_more.jsonl', 'a') as lfile:
                #         lfile.write(json.dumps({wd_form['form_uri']: row})+'\n')


with open('intersection_forms_gramm_comparison.json', 'w') as file:
   json.dump(matching_forms_output, file, indent=2)
with open('intersection_forms_missing_on_wikidata.json', 'w') as file:
   json.dump(formreps_missing_on_wikidata, file, indent=2)
