import csv

tags = {'prs': 'Q192613', 'act': 'Q1317831', 'ind': 'Q682111', '1': 'Q21714344', 'sg': 'Q110786', 'ptcp': 'Q2215850',
        'acc': 'Q146078',
        'n': 'Q1775461', 'pl': 'Q146786', 'sbjv': 'Q473746', 'voc': 'Q185077', 'm': 'Q499327', 'f': 'Q1775415',
        'abl': 'Q156986', '3': 'Q51929074',
        '2': 'Q51929049', 'iprf': 'Q12547192', 'nom': 'Q131105', 'gen': 'Q146233', 'dat': 'Q145599', 'pass': 'Q1194697',
        'imp': 'Q22716',
        'fut': 'Q501405', 'inf': 'Q179230', 'gdv': 'Q731298', 'ger': 'Q1923028', 'pprf': 'Q1823571', 'prf': 'Q625420',
        'fprf': 'Q1234617',
        'sup': 'Q1817208'}

with open("enhanced_forms.csv") as file:
    csvrows = csv.DictReader(file, delimiter=",")
    tags_count = {}
    for row in csvrows:
        taglist = row["cell"]
        taglisttags = taglist.split(".")
        for tag in taglisttags:
            if tag in tags_count:
                tags_count[tag] += 1
            else:
                tags_count[tag] = 1
print(tags_count)

# {'prs': 853192, 'act': 1466255, 'ind': 614694, '1': 312764, 'sg': 1322836, 'ptcp': 974245, 'acc': 287467, 'n': 520641,
#  'pl': 1334526, 'sbjv': 405366, 'voc': 244359, 'm': 499358, 'f': 499358, 'abl': 287469, '3': 377501, '2': 447740,
#  'iprf': 277418, 'nom': 244359, 'gen': 280774, 'dat': 248851, 'pass': 688817, 'imp': 117945, 'fut': 446195,
#  'inf': 42822, 'gdv': 545112, 'ger': 60532, 'pprf': 127836, 'prf': 386513, 'fprf': 63918, 'sup': 13390}
