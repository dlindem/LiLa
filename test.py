import requests

url = "https://lilamorph.wikibase.cloud/query/sparql?format=json&query=PREFIX%20rdfs%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2F2000%2F01%2Frdf-schema%23%3E%0APREFIX%20ontolex%3A%20%3Chttp%3A%2F%2Fwww.w3.org%2Fns%2Flemon%2Fontolex%23%3E%0APREFIX%20wikibase%3A%20%3Chttp%3A%2F%2Fwikiba.se%2Fontology%23%3E%0APREFIX%20lmwb%3A%20%3Chttps%3A%2F%2Flilamorph.wikibase.cloud%2Fentity%2F%3E%0APREFIX%20lmdp%3A%20%3Chttps%3A%2F%2Flilamorph.wikibase.cloud%2Fprop%2Fdirect%2F%3E%0A%0Aselect%20%3Flila_lemma_id%20%3Fform%20%3Fform_rep%20(group_concat(distinct%20%3Fudp_label%3BSEPARATOR%3D%22%7C%22)%20as%20%3Fudp_maps)%0A%20%20%20%20%20%20%20%0Awhere%20%7B%20bind(%27lemma%2F87035%27%20as%20%3Flila_lemma_id)%0A%20%20%3Flexeme%20lmdp%3AP1%20%3Flila_lemma_id%3B%20lmdp%3AP14%20lmwb%3AQ9%3B%20ontolex%3AlexicalForm%20%3Fform.%0A%20%20%3Fform%20ontolex%3Arepresentation%20%3Fform_rep%3B%20wikibase%3AgrammaticalFeature%20%5Blmdp%3AP9%20%3Fudp_map%5D.%20%3Fudp_map%20rdfs%3Alabel%20%3Fudp_label.%20filter%20(lang(%3Fudp_label)%3D%22en%22)%20%0A%20%20%0A%7D%20group%20by%20%3Flila_lemma_id%20%3Fform%20%3Fform_rep%20%3Fudp_maps%0A%0A"

r = requests.get(url)

print(r.json())