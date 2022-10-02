# script to generate the OOV dataset for LCQUAD - Could def be refactored and included in the main generation script (lcquad/build_dataset.py)

import json
import math
from typing import Dict, List

from classes.entry import Entry, Query, Question
from classes.monument_dataset import MonumentDataset
from common.consts import FIND_RESOURCES_BTW_ANGLE_BRACKETS_RE
import random

from common.utils import extract_alt_name, reduce_uri

# get subclasses of place: 
# select distinct ?domain where { {?domain rdfs:subClassOf dbo:Monument} UNION {?domain rdfs:subClassOf dbo:Place.}}

# SELECT RESOURCES
# SELECT DISTINCT ?x ?label WHERE { 
# ?subclass rdfs:subClassOf dbo:Place .
# ?x a ?subclass  . 
# ?x rdfs:label ?label. 
# filter langMatches( lang(?label), "EN" ) 
# } LIMIT 1000

def question_query_replace(entry: Entry, descr: str, replacement: Dict) -> Entry:
    replacement["value"] = reduce_uri(replacement["value"])

    # question
    entry.question.question = entry.question.question.replace(f'<{descr}>', f'<{replacement["label"]}>')
    entry.question.uri_question_only_resources = entry.question.uri_question_only_resources.replace(f'<{descr}>', f'<{replacement["value"]}>')
    entry.question.uri_question_rest_no_resources = entry.question.uri_question_rest_no_resources.replace(f'<{descr}>', f'<{replacement["label"]}>')
    entry.question.uri_question_all = entry.question.uri_question_all.replace(f'<{descr}>', f'<{replacement["value"]}>')

    # query
    entry.query.interm_sparql = entry.query.interm_sparql.replace(f'<{descr}>', f'<{replacement["value"].replace(":", "_")}>')
    entry.query.uri_interm_sparql_only_resources = entry.query.uri_interm_sparql_only_resources.replace(f'<{descr}>', f'<{replacement["value"]}>')
    entry.query.uri_interm_sparql_rest_no_resources = entry.query.uri_interm_sparql_rest_no_resources.replace(f'<{descr}>', f'<{replacement["value"].replace(":", "_")}>')
    entry.query.uri_interm_sparql_all = entry.query.uri_interm_sparql_all.replace(f'<{descr}>', f'<{replacement["value"]}>')
    entry.query.pure_sparql = entry.query.pure_sparql.replace(f'<{descr}>', f'<{replacement["value"]}>')

    return entry

if __name__ == "__main__":
    # TODO: Un-hardcode, add parameters, make fun to use
    with open('out_data/Monument/ontologies.json', 'r') as f:
        ontologies = json.load(f)

    with open('out_data/Monument/resources.json', 'r') as f:
        instances = json.load(f)

    with open('out_data/Monument/base/dataset.json', 'r') as f:
        dataset_base = json.load(f)

    with open('out_data/Monument/50/dataset.json', 'r') as f:
        dataset_50 = json.load(f)

    with open('out_data/Monument/80/dataset.json', 'r') as f:
        dataset_80 = json.load(f)

    with open('out_data/Monument/templates.json', 'r') as f:
        templates = json.load(f)

    # oov can be used on any monument dataset
    dataset = dataset_base + dataset_50 + dataset_80

    dataset_resources = []
    dataset_properties = []

    # get used KB elems from original dataset
    for entry in dataset:
        tokens = entry['question']['uri_question_all'].split()

        resources = [t for t in tokens if t[:3] is 'dbr']
        dataset_resources.extend(resources)

        properties = [t for t in tokens if t[:3] is 'dbo' or t[:3] is 'dbc' or t[:3] is 'dbp']
        dataset_properties.extend(properties)

    ontologies_sparql = ontologies['results']['bindings']
    resources_sparql = instances['results']['bindings']

    ontologies = []
    instances = []

    # Get uri and label for each KB elem
    for o in ontologies_sparql:
        value = reduce_uri(o['domain']['value'])
        label = extract_alt_name(*value.split(':', 1))
        if value not in dataset_properties:
            ontologies.append({
                'value': value,
                'label': label
            })

    for r in resources_sparql:
        value = reduce_uri(r['x']['value'])
        if value not in dataset_resources:
            instances.append({
                'value': value,
                'label': r['label']['value']
            })

    # Generate Dataset
    DATASET_SIZE = 250
    N_EXAMPLES_PER_TEMPLATE = math.ceil(DATASET_SIZE / len(templates))
    oov_test_set: List[Entry] = []

    for _ in range(N_EXAMPLES_PER_TEMPLATE):
        for t in templates:
            question = Question(question=t['question_template'],
                                uri_question_only_resources=t['question_template'],
                                uri_question_rest_no_resources=t['uri_question_template'],
                                uri_question_all=t['uri_question_template'])

            query = Query(interm_sparql=t['interm_sparql_template'],
                          uri_interm_sparql_only_resources= t['interm_sparql_template'],
                          uri_interm_sparql_rest_no_resources=t['uri_interm_sparql_template'],
                          uri_interm_sparql_all=t['uri_interm_sparql_template'],
                          pure_sparql=t['pure_sparql_template'])

            entry = Entry(
                id_val=f'_{len(oov_test_set)}',
                template_id_val=t['_id'],
                question_val=question,
                query_val=query,
                train_test_valid_set_val='test',
            )

            placeholders = FIND_RESOURCES_BTW_ANGLE_BRACKETS_RE.findall(t['question_template'])

            for p in placeholders:
                if 'ontology' in p:
                    entry = question_query_replace(entry, p, random.choice(ontologies))
                elif 'resource' in p:
                    entry = question_query_replace(entry, p, random.choice(instances))
                else:
                    raise Exception("UNKNOWN TAG:", p)

            entry.question.question = entry.question.question.replace('>', '').replace('<', '').lower()
            entry.question.uri_question_all = entry.question.uri_question_all.replace('>', '').replace('<', '')
            entry.question.uri_question_rest_no_resources = entry.question.uri_question_rest_no_resources.replace('>', '').replace('<', '')
            entry.question.uri_question_only_resources = entry.question.uri_question_only_resources.replace('>', '').replace('<', '')

            entry.query.interm_sparql = entry.query.interm_sparql.replace('>', '').replace('<', '')
            entry.query.uri_interm_sparql_all = entry.query.uri_interm_sparql_all.replace('>', '').replace('<', '')
            entry.query.uri_interm_sparql_only_resources = entry.query.uri_interm_sparql_only_resources.replace('>', '').replace('<', '')
            entry.query.uri_interm_sparql_rest_no_resources = entry.query.uri_interm_sparql_rest_no_resources.replace('>', '').replace('<', '')
            entry.query.pure_sparql = entry.query.pure_sparql.replace('>', '').replace('<', '')

            oov_test_set.append(entry)


    random.shuffle(oov_test_set)
    oov_test_set = oov_test_set[:DATASET_SIZE]
    dataset = MonumentDataset()
    dataset.entries = oov_test_set
    dataset.save('out_data/Monument/oov_dataset.json')