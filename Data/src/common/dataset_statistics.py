# Quick script to get some quick stats on your dataset (set sizes, template lenghts, intersection rate)

import json
from typing import List

from common.consts import FIND_RESOURCES_BTW_ANGLE_BRACKETS_RE
DATASET = 'out_data/Monument/80/dataset.json'
DATASET_OOV  = 'out_data/Monument/oov_dataset.json'
TEMPLATES = 'out_data/Monument/templates.json'
TAGS = ['dbo:', 'dbp:', 'dbr:', 'dbc:']

def get_intersection_rate_monument(train_set: List, test_set: List, tags=TAGS) -> float:
    kb_elems_train = set()

    for entry in train_set:
        kb_elems = [w for w in entry['question']['uri_question_all'].split() if w[:4] in tags]

        for e in kb_elems:
            kb_elems_train.add(e.strip())

    kb_elems_test = set()

    for entry in test_set:
        kb_elems = [w for w in entry['question']['uri_question_all'].split() if w[:4] in tags]

        for e in kb_elems:
            kb_elems_test.add(e.strip())

    print('in train', len(kb_elems_train))
    print('in test', len(kb_elems_test))

    print('only in train:', len(kb_elems_train - kb_elems_test))
    print('only in test:', len(kb_elems_test - kb_elems_train))
    print('common:', len(kb_elems_train - (kb_elems_train - kb_elems_test)))
    
    return 1 - len(kb_elems_test - kb_elems_train)/len(kb_elems_test)

def get_intersection_rate_lcquad(train_set: List, test_set: List) -> float:
    kb_elems_train = set()
    kb_elems_test = set()

    for entry in train_set:
        kb_elems = FIND_RESOURCES_BTW_ANGLE_BRACKETS_RE.findall(entry['original_data']['lcquad.sparql_query'])
        for e in kb_elems:
            kb_elems_train.add(e.strip())

    for entry in test_set:
        kb_elems = FIND_RESOURCES_BTW_ANGLE_BRACKETS_RE.findall(entry['original_data']['lcquad.sparql_query'])
        for e in kb_elems:
            kb_elems_test.add(e.strip())

    print('in train', len(kb_elems_train))
    print('in test', len(kb_elems_test))

    print('only in train:', len(kb_elems_train - kb_elems_test))
    print('only in test:', len(kb_elems_test - kb_elems_train))
    print('common:', len(kb_elems_train - (kb_elems_train - kb_elems_test)))

    return 1 - len(kb_elems_test - kb_elems_train)/len(kb_elems_test)


if __name__ == "__main__":
    with open(DATASET, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    with open(DATASET_OOV, 'r', encoding='utf-8') as f:
        test_set_oov = json.load(f)

    with open(TEMPLATES, 'r', encoding='utf-8') as f:
        templates = json.load(f)

    print("FOR DATASET ", DATASET)
    train_set = [e for e in dataset if e['set'] == 'train']
    test_set = [e for e in dataset if e['set'] == 'test']
    print("SIZE TRAIN :", len(train_set))
    print("SIZE VALID :", len([e for e in dataset if e['set'] == 'valid']))
    print("SIZE TEST :", len(test_set))

    # minus 1 bcs we dont count the ? as a word
    #print("LONGEST TEMPLATE:", max([len(t['question_template'].split()) - 1  for t in templates]))
    #print("SHORTEST TEMPLATE:", min([len(t['question_template'].split()) - 1 for t in templates]))
    print("INTERSECTION RATE:", get_intersection_rate_monument(train_set, test_set_oov) )
