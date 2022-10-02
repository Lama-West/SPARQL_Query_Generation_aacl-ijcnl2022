# Attempt at building a word based tagging algorithm, not scalable NOR working yet

from typing import Dict, Tuple, Union, Optional, Set, List, cast
from Levenshtein import distance as levenshtein_distance
from spacy.lang.en import English
from classes.entry import Entry
from common.consts import GET_RESOURCES_PURE_SPARQL_RE, SPARQL_TYPE
from common.utils import extract_alt_name, gen_beg_end, reduce_uri
from spacy.tokens import Doc

from classes.dataset import Dataset
from classes.lcquad_dataset import LCQUADDataset, correct_resources_tags

nlp = English()
tokenizer = nlp.tokenizer
stopwords = nlp.Defaults.stop_words

Template = Dict[str, Union[str, int, List[str]]]

def get_template_from_id(templates: List[Template], id: Union[str, int]) -> Template:
    return [t for t in templates if t['id'] == id][0]


def add_resources_from_templates(resources_dict: Dict[str, Set[str]], templates: List[Template], entry: Entry) -> Tuple[List[str], Dict[str, Set[str]]]:
    template = get_template_from_id(templates, entry.template_id)

    resources = LCQUADDataset.RE_ONLY_RESOURCES.findall(entry.get_from_original_data('lcquad','intermediary_question'))
    resources = [r[1:-1] for r in resources] # remove <>

    resources_tags = cast(List[str], template['resource_tags'])
    resources_tags = correct_resources_tags(resources_tags, entry.template_id, len(resources))

    assert len(resources_tags) == len(resources)

    resources_with_tags = list(zip(resources_tags, resources))

    uris: List[str] = LCQUADDataset.RE_ONLY_RESOURCES.findall(entry.get_from_original_data('lcquad','sparql_query'))
    uris = [uri[1:-1] for uri in uris]
    uris = [reduce_uri(u) for u in uris if u != SPARQL_TYPE]

    uris_tags: List[str] = LCQUADDataset.RE_ONLY_RESOURCES.findall(str(template['template']).replace('class', '<class>'))
    assert len(uris_tags) == len(uris)

    uris_with_tags = list(zip(uris_tags, uris))
    uris_with_tags = [(tag, uri) for tag, uri in uris_with_tags if uri != 'dbp:type']

    for u_tag, uri in uris_with_tags:
        alt_name = extract_alt_name(*uri.split(':', 1))
        expressions: Set[str] = resources_dict.get(uri, set([]))

        if len(alt_name) > 0:
            expressions.add(alt_name.lower())

        for r_tag, resource in resources_with_tags:
            if r_tag == u_tag:
                if len(resource) > 0:
                    expressions.add(resource.lower())
                break

        resources_dict[uri] = expressions

    return uris, resources_dict


def add_resources_from_sparql(resources_dict: Dict[str, Set[str]], entry: Entry) -> Tuple[List[str], Dict[str, Set[str]]]:
    entities_match = GET_RESOURCES_PURE_SPARQL_RE.findall(entry.pure_sparql)
    uris: List[str] = [uri[0] for uri in entities_match]

    for uri in uris:
        alt_name = extract_alt_name(*uri.split(':', 1))
        expressions: Set[str] = resources_dict.get(uri, set([]))

        if len(alt_name) > 0:
            expressions.add(alt_name.lower())

        resources_dict[uri] = expressions

    return uris, resources_dict


def enrich_with_levenshtein(tokens: Doc, tuple_indices: List[Tuple[int, int]], resources_dict: Dict[str, Set[str]], uris: List[str], should_print=False) -> Dict[str, Set[str]]:
    for beg, end in tuple_indices:
        possible_ressource = ''.join(t.text_with_ws for t in tokens[beg:end]).lower().strip()
        found_match = False
        possible_expressions = {uri: resources_dict.get(uri, set([])) for uri in uris}

        for uri in possible_expressions:
            for expr in possible_expressions[uri]:
                if levenshtein_distance(possible_ressource.lower(), expr.lower()) < 2:
                    found_match = True
                    expressions = resources_dict.get(uri, set([]))
                    expressions.add(possible_ressource.lower())
                    resources_dict[uri] = expressions
                    break

                if '&' in expr:
                    if levenshtein_distance(possible_ressource.lower(), expr.replace('&','and').lower()) < 2:
                        found_match = True
                        expressions = resources_dict.get(uri, set([]))
                        expressions.add(possible_ressource.lower())
                        resources_dict[uri] = expressions
                        break

                if '-' in expr:
                    if levenshtein_distance(possible_ressource.lower(), expr.replace(' \u2013 ',' ').lower()) < 2:
                        found_match = True
                        expressions = resources_dict.get(uri, set([]))
                        expressions.add(possible_ressource.lower())
                        resources_dict[uri] = expressions
                        break

                if '.' in expr:
                    if levenshtein_distance(possible_ressource.lower(), expr.replace('.','').lower()) < 2:
                        found_match = True
                        expressions = resources_dict.get(uri, set([]))
                        expressions.add(possible_ressource.lower())
                        resources_dict[uri] = expressions
                        break

            if found_match:
                break

    return resources_dict


def enrich_with_subwords(tokens: Doc, tuple_indices: List[Tuple[int, int]], resources_dict: Dict[str, Set[str]], uris: List[str]) -> Dict[str, Set[str]]:
    for beg, end in tuple_indices:
        possible_ressource = ''.join(t.text_with_ws for t in tokens[beg:end]).lower().strip()
        found_match = False
        possible_expressions = {uri: resources_dict.get(
            uri, set([])) for uri in uris}

        for uri in possible_expressions:
            for expr in possible_expressions[uri]:
                if possible_ressource.strip().lower() in expr:
                    found_match = True
                    expressions = resources_dict.get(uri, set([]))
                    expressions.add(possible_ressource.lower())
                    resources_dict[uri] = expressions
                    break

            if found_match:
                break
    return resources_dict


def build_resources_dict(dataset: Dataset, templates: Optional[List[Dict]] = None) -> Dict[str, Set[str]]:
    if templates is not None and not isinstance(dataset, LCQUADDataset):
        print("[WARNING] The build_resources_dict method assumes the dataset is of format LCQuAD if you use templates!")

    resources_dict: Dict[str, Set[str]] = {}
    for entry in dataset.entries:
        if templates is not None:
           uris, resources_dict = add_resources_from_templates(resources_dict, templates, entry)
        else: 
            uris, resources_dict = add_resources_from_sparql(resources_dict, entry)

        tokens = nlp(entry.question)
        idx = gen_beg_end(len(tokens))

        should_print = entry.id == "3049"

        if should_print:
            print(uris)
            print([ resources_dict[u] for u in uris])

        resources_dict = enrich_with_levenshtein(tokens, idx, resources_dict, uris, should_print)
        resources_dict = enrich_with_subwords(tokens, idx, resources_dict, uris)

    return resources_dict


def filter_resources(resources_dict: Dict[str, Set[str]]) -> Dict[str, List[str]]:
    filtered_dict: Dict[str, List[str]] = {}

    for key in resources_dict:
        resources_list : List[str] = sorted(list(resources_dict[key]), key=len, reverse=True)
        resources_list = [r for r in resources_list if r not in stopwords and len(
            r.replace('.', '')) >= 2]

        filtered_dict[key] = resources_list

    return filtered_dict


def build_uri_vocab(dataset: Dataset, templates: Optional[List[Dict]] = None) -> Dict[str, List[str]]:
    resources_dict = build_resources_dict(dataset, templates)
    return filter_resources(resources_dict)
