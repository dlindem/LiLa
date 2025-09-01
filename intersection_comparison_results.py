import json, time
from importlib.metadata import entry_points

with open('intersection_forms_gramm_comparison.json') as file:
    data = json.load(file)
    results = {}
    for entry in data:
        if entry['deviation'] not in results:
            results[entry['deviation']] = [entry]
        else:
            results[entry['deviation']].append(entry)
seen_form_uri = {}
improved_results = {}
duplicated = []
for deviation_value in sorted(results.keys()):
    print(f"Deviation {deviation_value}: {len(results[deviation_value])} lila morph lines")

    improved_results[deviation_value] = {}
    for result_entry in results[deviation_value]:
        form_uri = list(result_entry.keys())[0]
        # print(form_uri)
        if form_uri in seen_form_uri and seen_form_uri[form_uri] == deviation_value:
           #  print(f"This one has another solution with the same deviation value {deviation_value}: \n{result_entry}")
            # print(improved_results[deviation_value][form_uri])
            improved_results[deviation_value][form_uri].append(result_entry)
            duplicated.append(result_entry[form_uri]['lila_row'])
        elif form_uri not in seen_form_uri:
            seen_form_uri[form_uri] = deviation_value
            improved_results[deviation_value][form_uri] = [result_entry]
        # elif form_uri in seen_form_uri:
          #  print("\nThis had a better solution (lower deviation)\n")

    with open(f'intersection_comparison_results_deviation_{deviation_value}.json', 'w') as file:
        json.dump(improved_results[deviation_value], file, indent=2)
    with open('duplicated_lila_rows_with_same_deviation.json', 'w') as file:
        json.dump(duplicated, file, indent=2)

for deviation_value in improved_results:
    print(f"Deduplicated results: Deviation {deviation_value}: {len(improved_results[deviation_value])} lila morph lines")