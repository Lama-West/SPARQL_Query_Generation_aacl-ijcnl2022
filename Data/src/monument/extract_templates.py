import argparse
import json
import re
from typing import Dict, List, Optional

from classes.monument_dataset import MonumentDataset
from common.consts import GET_RESOURCES_INTERM_SPARQL_RE, GET_RESOURCES_PURE_SPARQL_RE
from common.re_callbacks import abstract_resources

Template = Dict[str, str]

def add_new_template(templates: List[Template], t_id:Optional[str] = None) ->  List[Template]:
    question_template = input('question template: ')
    question_regex = generate_question_regex(question_template)

    if t_id is None:
        pure_sparql_template_id = input('sparql template id (blank for new sparql): ')

        if len(pure_sparql_template_id) == 0: # create new template
            interm_sparql_template = input('interm sparql template: ')
            pure_sparql_template = input('pure sparql template: ')
            regex_interm_sparql = '' if interm_sparql_template == '' else generate_interm_sparql_regex(interm_sparql_template)
            regex_pure_sparql = '' if pure_sparql_template == '' else generate_pure_sparql_regex(pure_sparql_template)

        else: # use sparql from existing template
            interm_sparql_template = [t['interm_sparql_template'] for t in templates if t['id'] == pure_sparql_template_id][0]
            pure_sparql_template = [t['pure_sparql_template'] for t in templates if t['id'] == pure_sparql_template_id][0]
            regex_interm_sparql = [t['regex_interm_sparql'] for t in templates if t['id'] == pure_sparql_template_id][0]
            regex_pure_sparql = [t['regex_pure_sparql'] for t in templates if t['id'] == pure_sparql_template_id][0]

    new_tid = str(len(templates))
    templates.append({
        '_id': new_tid,
        'question_template': question_template,
        'interm_sparql_template': interm_sparql_template,
        'pure_sparql_template': pure_sparql_template,
        'regex_english': question_regex,
        'regex_interm_sparql': regex_interm_sparql,
        'regex_pure_sparql': regex_pure_sparql
    })

    return templates


def add_question_reformulations(dataset: MonumentDataset, templates:  List[Template]):

    for entry in dataset.entries:
        t_id = None

        # FIND TEMPLATE AND SEE IF NEW FORMULATION
        for t in templates:
            if re.match(t['regex_english'], entry.question):
                t_id = t['id']
                break

        # IF NEVER SEEN BEFORE FORMULATION
        if t_id is None:
            print("NO TEMPLATE FOUND: ", entry.question)
            add_new_template_str = input("Add new template? y/n... ")

            if add_new_template_str.lower() == 'y':
                templates = add_new_template(templates)

    return templates


def generate_question_regex(question_template: str)-> str:
    regex = question_template.replace('?', '\?')
    regex = regex.replace('.', '\.')
    regex = re.sub('<.*?>', '(.*?)', regex)
    regex = regex + '$'
    return regex


def generate_interm_sparql_regex(interm_sparql_template: str)-> str:
    regex = interm_sparql_template.replace('[', '\[')
    regex = regex.replace(']', '\]')
    regex = regex.replace(')', '\)')
    regex = regex.replace('(', '\(')
    regex = regex.replace('*', '\*')
    regex = regex.replace('?', '\?')
    regex = regex.replace('.', '\.')
    regex = regex.replace('|', '\|')
    regex = re.sub('<.*?>', '(.*?)', regex)
    regex = regex + '$'
    return regex


def generate_pure_sparql_regex(pure_sparql_template: str)-> str:
    regex = pure_sparql_template.replace('[', '\[')
    regex = regex.replace(']', '\]')
    regex = regex.replace(')', '\)')
    regex = regex.replace('(', '\(')
    regex = regex.replace('*', '\*')
    regex = regex.replace('?', '\?')
    regex = regex.replace('.', '\.')
    regex = regex.replace('|', '\|')
    regex = re.sub('<.*?>', '(.*?)', regex)
    regex = regex + '$'
    return regex


def check_for_missed_formulations(dataset: MonumentDataset, templates_path: str) -> None:
    with open(templates_path, 'r') as f:
        templates:  List[Template] = json.load(f)

    for t in templates:
        t['question_regex'] = generate_question_regex(t['question_template'])
        t['interm_sparql_regex'] = generate_interm_sparql_regex(t['interm_sparql_template'])
        t['pure_sparql_regex'] = generate_pure_sparql_regex(t['pure_sparql_template'])

    templates = add_question_reformulations(dataset, templates)

    with open(templates_path, 'w') as f:
        json.dump(templates, f, indent=4)


def use_placeholders(dataset: MonumentDataset) -> List[Template]:
    templated_entries: List[Template] = []

    for entry in dataset.entries:
        templated_interm_sparql = GET_RESOURCES_INTERM_SPARQL_RE.sub(abstract_resources, entry.interm_sparql)
        templated_interm_sparql = re.sub('\s+', ' ', templated_interm_sparql)

        templated_pure_sparql = GET_RESOURCES_PURE_SPARQL_RE.sub(abstract_resources, entry.pure_sparql)
        templated_pure_sparql = re.sub('\s+', ' ', templated_pure_sparql)

        templated_entries.append({
            '_id': entry.id,
            'interm_sparql_template': templated_interm_sparql,
            'pure_sparql_template': templated_pure_sparql
        })

    return templated_entries


def reduce_templates(dataset: MonumentDataset, templated_entries: List[Template]):
    templates:  List[Template] = []

    for possible_template in templated_entries:
        if possible_template['sparql_template'] not in [t['sparql_template'] for t in templates]:
            templates.append({
                '_id': str(len(templates) + 1),
                'question_example': dataset.get_entry_at_id(possible_template['_id']).question,
                'interm_sparql_template': possible_template['interm_sparql_template'],
                'pure_sparql_template':possible_template['pure_sparql_template'],
            })

    return templates


def generate_templates(dataset: MonumentDataset, templates_path: str) -> None:
    templated_entries = use_placeholders(dataset)
    templates = reduce_templates(dataset, templated_entries)

    with open(templates_path, 'w', encoding='utf-8') as f:
        json.dump(templates, f, indent=4)


def main(args):
    dataset = MonumentDataset(args.nl, args.sparql)

    if args.step == 1:
        generate_templates(dataset, args.templates)
        print("BEFORE NEXT STEP - Handmake NL templates (convert question_example to question_template)")

    elif args.step == 2:
        check_for_missed_formulations(dataset, args.templates)
        print("BEFORE NEXT STEP - Reorder templates (from least capturing to most capturing) !! you might need to redo this step !!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract templates from monument dataset")

    parser.add_argument('--step', '--s', type=int, choices=[1,2], help='which step are you at: 1 or 2')

    parser.add_argument("--nl", type=str, default='raw_data/Monument/base/data.en',
                        help="path to the json file containing the train original lcquad dataset")

    parser.add_argument("--sparql", type=str, default='raw_data/Monument/base/data.sparql',
                        help="path to the json file containing the test original lcquad dataset")

    parser.add_argument("--templates", type=str, default='out_data/Monument/templates.json',
                        help="path to templates file")

    args = parser.parse_args()

    if not args.nl or not args.sparql:
        parser.error(
            "This program requires values for --nl and --sparql")

    main(args)
