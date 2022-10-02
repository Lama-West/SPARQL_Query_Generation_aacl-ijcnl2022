# script to generate the OOV dataset for LCQUAD - Could def be refactored and included in the main generation script (lcquad/build_dataset.py)
import json
import math
from typing import Dict, List, Tuple
from classes.entry import Entry, Flags, Query, Question
from classes.lcquad_dataset import LCQUADDataset
from common.interm_sparql_to_pure_sparql import escape_query
from common.query_dbpedia import query_dbpedia
from common.consts import FIND_RESOURCES_BTW_ANGLE_BRACKETS_RE
from tqdm import tqdm
import random

from common.utils import extract_alt_name

# TODO: Could be ran by the script
# REQUEST TO GET PROPERTIES
# select distinct ?domain ?property ?range where {
# ?property a owl:ObjectProperty.
# ?property rdfs:range ?range.
# ?range a owl:Class.
# ?property rdfs:domain ?domain.

# } LIMIT 1000

ENDPOINT = "http://dbpedia.org/sparql"
GRAPH = "http://dbpedia.org"
GET_INSTANCES_OF_CLASS = "SELECT DISTINCT ?x ?label WHERE {{ ?x a {template} . ?x rdfs:label ?label. filter langMatches( lang(?label), \"EN\" ) }} LIMIT 100"
#%%
def reduce_uri(uri: str) -> str:
    uri = uri.replace('http://dbpedia.org/ontology/', 'dbo:')
    uri = uri.replace('http://dbpedia.org/category/', 'dbc:')
    uri = uri.replace('http://dbpedia.org/resource/', 'dbr:')
    return uri.replace('http://dbpedia.org/property/', 'dbp:')

#%%
def query_for_instances(clss: str) -> List:
    clss = clss.replace('(', '\\(')
    clss = clss.replace(')', '\\)')
    clss = clss.replace("'", "\\'")
    clss = clss.replace(",", "\\,")

    query = GET_INSTANCES_OF_CLASS.format(template=clss)
    result = query_dbpedia(query)

    return [{'label':value['label']['value'], 'value': value['x']['value']} for value in result['results']['bindings']]

#%%
def question_query_replace(entry: Entry, idx: str, descr: str, replacement: Dict) -> Entry:
    replacement["value"] = reduce_uri(replacement["value"])
    uri = f'<{replacement["value"]}>'
    label = f'{replacement["label"]}'
    descr = f'<{descr}>'
    idx_descr = f'<{idx}>'

    rplc = uri if descr in entry.question.interm_question and idx_descr in entry.query.interm_sparql else label.lower()

    # question
    entry.question.interm_question = entry.question.interm_question.replace(descr, label.lower())
    entry.question.uri_question_all = entry.question.uri_question_all.replace(descr, rplc)
    
    if replacement["value"][:3] == 'dbr':
        entry.question.uri_question_only_resources = entry.question.uri_question_only_resources.replace(descr, rplc)
        entry.question.uri_question_rest_no_resources = entry.question.uri_question_rest_no_resources.replace(descr, label)
    else:
        entry.question.uri_question_only_resources = entry.question.uri_question_only_resources.replace(descr, label.lower())
        entry.question.uri_question_rest_no_resources = entry.question.uri_question_rest_no_resources.replace(descr, rplc)

    # query
    entry.query.interm_sparql = entry.query.interm_sparql.replace(idx_descr, uri)
    entry.query.interm_sparql = entry.query.interm_sparql.replace(descr, uri)
    entry.query.pure_sparql = entry.query.pure_sparql.replace(idx_descr, uri)
    entry.query.pure_sparql = entry.query.pure_sparql.replace(descr, uri)

    return entry

#%%
def extract_KB_elems_from_dataset(dataset: List[Dict]) -> Tuple[List[str], List[str]]:
    dataset_properties = []
    dataset_resources = []

    for entry in dataset:
        if entry['set'] == 'train':
            sparql = entry['original_data']['lcquad']['sparql_query']
            resources = FIND_RESOURCES_BTW_ANGLE_BRACKETS_RE.findall(sparql)
            for r in resources: 
                if '/resource/' in r:
                    dataset_resources.append(r)
                else:
                    dataset_properties.append(r)

    return dataset_properties, dataset_resources

#%%
def extract_KB_triples_from_dbpedia(out_data: Dict) -> Tuple[Dict, Dict]:

    results = out_data['results']['bindings']
    domains: Dict = {}
    instances: Dict = {}

    for r in results:
        domain = reduce_uri(r['domain']['value'])
        prop = reduce_uri(r['property']['value'])
        rnge = reduce_uri(r['range']['value'])

        prop_label = extract_alt_name(*prop.split(':', 1))
        rnge_label = extract_alt_name(*rnge.split(':', 1))

        if domain not in dataset_properties and prop not in dataset_properties and rnge not in dataset_properties:
            possible_prob = domains.get(domain, [])
            possible_prob.append(
                {
                    'property': {
                        'value': prop,
                        'label': prop_label
                    },'range': {
                        'value': rnge,
                        'label': rnge_label
                    }
                })

            domains[domain] = possible_prob
            instances[domain] = []
            instances[rnge] = []

    return domains, instances

#%%
def remove_classes_without_resources(domains: Dict, instances: Dict, dataset_resources: List[str]) -> Tuple[Dict, Dict]:
    for key in tqdm(instances):
        resources = query_for_instances(key)
        resources = [r for r in resources if r not in dataset_resources]

        if len(resources) == 0:
            new_domains = {}

            for dom in domains:
                if dom != key:
                    new_triplets = []

                    for triplet in domains[dom]:
                        if triplet['range']['value'] != key:
                            new_triplets.append(triplet)

                    if len(new_triplets) > 0:
                        new_domains[dom] = new_triplets

            domains = new_domains

        else:
            instances[key] = resources

    return domains, instances

#%%
def generate_entry_from_template(domains: Dict, instances: Dict) -> Entry:
    placeholders = FIND_RESOURCES_BTW_ANGLE_BRACKETS_RE.findall(t['question_template']) + FIND_RESOURCES_BTW_ANGLE_BRACKETS_RE.findall(t['template'])
    placeholders = [p for p in placeholders if '|' in p]

    if t['id'] == 106 or t['id'] == 406:
        domain = random.choice([d for d in domains if any([triplets['range']['value'] == d for triplets in domains[d]])])
        triplet = random.choice([t for t in domains[domain] if t['range']['value'] == domain])
        prop, rnge = triplet['property'], triplet['range']

    elif any(['property_1' in p or 'property_2' in p for p in placeholders]):
        domain = random.choice([d for d in domains if len(domains[d]) > 1])
        trip_1, trip_2 = random.choices(domains[domain], k=2)
        prop_1, rnge_1 = trip_1['property'], trip_1['range']
        prop_2, rnge_2 = trip_2['property'], trip_2['range']

    else:
        domain = random.choice(list(domains))
        triplet = random.choice(domains[domain])
        prop, rnge = triplet['property'], triplet['range']

    question = Question(
        interm_question=t['question_template'],
        uri_question_only_resources=t['question_template'],
        uri_question_rest_no_resources=t['question_template'],
        uri_question_all=t['question_template'])

    query = Query(
        interm_sparql=t['template'],
        uri_interm_sparql_all=t['template'],
        uri_interm_sparql_only_resources=t['template'],
        pure_sparql=t['template'])

    entry = Entry(
        id_val=None,
        template_id_val=t['id'],
        question_val=question,
        query_val=query,
        train_test_valid_set_val='test'
    )

    for p in placeholders:
        idx, ttype = p.split('|')
        if ttype == 'domain':
            domain_dict = {
                'value': domain,
                'label': extract_alt_name(*domain.split(':', 1))
            }
            entry = question_query_replace(entry, idx, p, domain_dict)

        elif ttype == 'property':
            entry = question_query_replace(entry, idx, p, prop)

        elif ttype == 'property_1':
            entry = question_query_replace(entry, idx, p, prop_1)

        elif ttype == 'property_2':
            entry = question_query_replace(entry, idx, p, prop_2)

        elif ttype == 'range':
            entry = question_query_replace(entry, idx, p, rnge)

        elif ttype == 'range_1':
            entry = question_query_replace(entry, idx, p, rnge_1)

        elif ttype == 'range_2':
            entry = question_query_replace(entry, idx, p, rnge_2)

        elif ttype == 'range:resource':
            res = random.choice(instances[rnge['value']])
            entry = question_query_replace(entry, idx, p, res)

        elif ttype == 'range_1:resource':
            res = random.choice(instances[rnge_1['value']])
            entry = question_query_replace(entry, idx, p, res)

        elif ttype == 'range_2:resource':
            res = random.choice(instances[rnge_2['value']])
            entry = question_query_replace(entry, idx, p, res)

        elif ttype == 'domain:resource':
            res = random.choice(instances[domain])
            entry = question_query_replace(entry, idx, p, res)
        else:
            raise Exception("UNKNOWN TAG:", ttype)

    return entry

#%%
#if __name__ == "__main__":
    # TODO: Un-hardcode, add parameters, make fun to use

# properties is the result of the query to get property defined at the top of this file

# %%
with open('../../out_data/LC-QuAD/properties.json', 'r') as f:
    out_data = json.load(f)

with open('../../out_data/LC-QuAD/dataset.json', 'r') as f:
    dataset = json.load(f)

with open('../../out_data/LC-QuAD/oov_templates.json', 'r') as f:
    templates = json.load(f)

# %%
dataset_properties, dataset_resources = extract_KB_elems_from_dataset(dataset)
domains, instances = extract_KB_triples_from_dbpedia(out_data)
domains, instances = remove_classes_without_resources(domains, instances, dataset_resources)

# %%
# GENERATE DATASET
GENERATED_SET_SIZE = 500
DATASET_SIZE = 250
N_EXAMPLES_PER_TEMPLATE = math.ceil(DATASET_SIZE / len(templates))
MAX_TRIES = 5
oov_test_set: List[Entry] = []
counter = 0
while counter < DATASET_SIZE:
    for t in templates:
        print('new entry!', len(oov_test_set))
        entry = generate_entry_from_template(domains, instances)
        entry.id = f'_{len(oov_test_set)}'

        result = query_dbpedia(escape_query(entry.query.pure_sparql.replace('<', '').replace('>', '')))
        if 'boolean' not in result:
            if len(result['results']['bindings']) == 0:
                print('failed :( - unable to generate query for template', t['id'])
                continue
            counter +=1
            oov_test_set.append(entry)

random.shuffle(oov_test_set)
oov_test_set = oov_test_set[:DATASET_SIZE]

#%%
oov_test_set_backup = oov_test_set[:]

#%%
oov_test_set = oov_test_set_backup

#%%
lcquad_empty = LCQUADDataset()
for entry in oov_test_set:

    entry.question.uri_question_all = entry.question.uri_question_all.replace('<', '').replace('>', '')
    entry.question.uri_question_only_resources = entry.question.uri_question_only_resources.replace('<', '').replace('>', '')
    entry.question.uri_question_rest_no_resources = entry.question.uri_question_rest_no_resources.replace('<', '').replace('>', '')
    flags = Flags(all_value=True)
    entry.query.uri_interm_sparql_all = lcquad_empty.generate_interm_sparql(entry.query.pure_sparql, True, flags)
    entry.query.uri_interm_sparql_only_resources = entry.query.uri_interm_sparql_all.replace('dbc:', 'dbc_').replace('dbp:', 'dbp_').replace('dbo:', 'dbo_')
    entry.query.uri_interm_sparql_rest_no_resources = entry.query.uri_interm_sparql_all.replace('dbr:', 'dbr_')
    entry.query.interm_sparql = entry.query.uri_interm_sparql_only_resources.replace('dbr:', 'dbr_')
    entry.query.pure_sparql = entry.query.pure_sparql.replace('<', '').replace('>', '')


#%%
template_count: Dict[str, int] = {}

# for entry in oov_test_set:
#     cnt = template_count.get(entry['template_id'], 0)
#     template_count['template_id'] = cnt+1

lcquad_empty.entries = oov_test_set
lcquad_empty.save('./oov_dataset.json')


# %%
