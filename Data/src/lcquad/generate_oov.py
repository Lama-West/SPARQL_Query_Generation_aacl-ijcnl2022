# script to generate the OOV dataset for LCQUAD - Could def be refactored and included in the main generation script (lcquad/build_dataset.py)
import json
from classes.entry import Flags
from classes.lcquad_dataset import LCQUADDataset

OUT = 'out_data/LC-QuAD/oov_dataset.json'

with open(OUT, 'r') as f:
    dataset = json.load(f)

lcquad_empty = LCQUADDataset()

fl = ['dbr:', 'dbc:', 'dbp:', 'dbo:']

for entry in dataset:
    flags = Flags(all_value=True)
    og = entry['query']['pure_sparql']

    for w in range(len(og.split())):
        word = og.split()[w]
        if word.startswith(tuple(fl)):
            og = og.replace(word, f'<{word}>')


    entry['query']['uri_interm_sparql_all'] = lcquad_empty.generate_interm_sparql(og, True, flags)
    print("ALL:", entry['query']['uri_interm_sparql_all'])

    entry['query']['uri_interm_sparql_only_resources'] = entry['query']['uri_interm_sparql_all'].replace('dbc:', 'dbc_').replace('dbp:', 'dbp_').replace('dbo:', 'dbo_')
    print("RESOURCES:", entry['query']['uri_interm_sparql_only_resources'])

    entry['query']['uri_interm_sparql_rest_no_resources'] =entry['query']['uri_interm_sparql_all'].replace('dbr:', 'dbr_')
    print("NO RESOURCES:", entry['query']['uri_interm_sparql_rest_no_resources'])

with open(f"{OUT}2", 'w') as f:
    json.dump(dataset, f, indent=4)
