# all util fonctions for regex callbacks!

import re
from typing import List, Tuple
from classes.entry import Flags
from common.consts import *


def escape_uri_for_regex(uri: str) -> str:
    uri = uri.replace('(', '\(')
    uri = uri.replace(')', '\)')
    uri = uri.replace('.', '\.')
    uri = uri.replace('?', '\?')
    uri = uri.replace('*', '\*')
    uri = uri.replace('+', '\+')
    uri = uri.replace("'", "\'")

    return uri


def convert_to_interm_sparql_except_resources(match: re.Match) -> str:
    interm_sparql: str = match.group(0).lower()

    for r in PURE_SPARQL_TO_INTERM:
        interm_sparql = interm_sparql.replace(
            r['pure_sparql'], r['interm_sparql'])

    interm_sparql = re.sub('\s+', ' ', interm_sparql)
    return interm_sparql


def encode_resources_in_interm_sparql(match: re.Match, keep_uris: bool, flags: Flags = None) -> str:
    resource: str = match.group(0)

    DBR_START = tuple(['dbr', '<dbr', '<http://dbpedia.org/resource/'])
    DBP_START = tuple(['dbp', '<dbp', '<http://dbpedia.org/property/'])
    DBC_START = tuple(['dbc', '<dbc', '<http://dbpedia.org/category/'])
    DBO_START = tuple(['dbo', '<dbo', '<http://dbpedia.org/ontology/'])

    if flags is not None:
        should_replace = flags.dbr and (resource.startswith(DBR_START))
        should_replace = should_replace or flags.dbp and (resource.startswith(DBP_START))
        should_replace = should_replace or flags.dbc and (resource.startswith(DBC_START))
        should_replace = should_replace or flags.dbo and (resource.startswith(DBO_START))

    elif keep_uris and flags is None:
        raise ValueError("Keep uris is true but no flags provided")
    else:
        should_replace = False

    for r in URI_SHORTENERS:
        if keep_uris and should_replace:
            resource = resource.replace(r['match'], r['pure_sparql'])
        else:
            resource = resource.replace(r['match'], r['interm_sparql'])

    if not keep_uris:
        for r in PURE_SPARQL_TO_INTERM_RES:
            resource = resource.replace(r['pure_sparql'], r['interm_sparql'])

    resource = re.sub('\s+', ' ', resource)

    return resource[1:-1]


def lowercase_except_resources(match: re.Match) -> str:
    sparql: str = match.group(0).lower()
    return sparql


def encode_resources_in_pure_sparql(match: re.Match) -> str:
    resource: str = match.group(0)

    for r in URI_SHORTENERS:
        resource = resource.replace(r['match'], r['pure_sparql'])

    return resource[1:-1]


def replace_resource_with_uri(match: re.Match, expressions: List[str], replacement: str) -> str:
    to_replace: str = ' ' + match.group(1)
    resource: str = match.group(2)

    for expr in expressions:
        if expr in to_replace:
            to_replace = re.sub(f'(\s{escape_uri_for_regex(expr)})', f' {replacement}', to_replace)
            break

    return to_replace + resource


def correct_parentheses_interm_sparql(match: re.Match) -> str:
    dt = {'par_open': 'sparql_open', 'par_close': 'sparql_close'}
    whole_match: str = match.group(0)
    original_span = match.span(0)
    span_open, span_close = match.span(1), match.span(2)

    return whole_match[: span_open[0] - original_span[0]] + dt[match.group(1)] + whole_match[span_open[1] - original_span[0] : span_close[0]- original_span[0]] + dt[match.group(2)] + whole_match[span_close[1]- original_span[0]:]


def replace_quotes(match: re.Match) -> str:
    whole_match = list(match.group(0))
    replacement = list(' sparql_quote ')
    offset = match.span(0)[0]

    for g in range(len(match.groups()), 0, -1):
        span = match.span(g)
        if span[0] == -1 or span[1] == -1:
            continue

        whole_match[span[0] - offset : span[1] - offset] = replacement

    return ''.join(whole_match)


def correct_sep_dots(match: re.Match) -> str:
    e = match.group(0).strip()
    if e[-1] == '.':
        if e in EXCEPTIONS_NOT_REPLACE:
            return f' {match.group(0)} '

        elif e[-2].isnumeric() or e.split('_')[-1].lower() in ENDS_EXCEPTIONS_REPLACE:
            return f' {e[:-1]} sep_dot '

        elif len(e.split('.')[-2]) <= 4:
            return f' {match.group(0)} '

        elif len(e.split('_')[-1]) <= 4 or e.split('_')[-1].lower() in ENDS_EXCEPTIONS_NOT_REPLACE:
            return f' {match.group(0)} '
        else:
            return f' {e[:-1]} sep_dot '

    return f' {match.group(0)} '


def remove_spaces_from_resources(match: re.Match) -> str:
    entity = match.group(0)
    entity = entity.replace(' ', '')
    entity = entity.replace('\\', '')
    return f' {entity} '


def insert_spaces_math(match: re.Match) -> str:
    out = ' '
    for m in match.groups():
        out += m
        out += ' '
    return out


def insert_resources(m: re.Match, resources: List[str]) -> str:
    whole_match = list(m.group(0))
    offset = 0

    for r in range(len(m.groups())):
        replacement_span = m.span(r + 1)
        whole_match[replacement_span[0] + offset:replacement_span[1] + offset] = list(resources[r])
        offset += len(resources[r]) - (replacement_span[1] -  replacement_span[0])

    return ''.join(whole_match)


def abstract_resources(match: re.Match) -> str:
    NO_REPLACE_PURE = ['dbo:abstract', 'dbp:length', 'dbo:location', 'dbo:designer', 'dbp:complete', 'dbp:nativename', 'dbp:height']
    NO_REPLACE_INTERM = ['dbo_abstract', 'dbp_length', 'dbo_location', 'dbo_designer', 'dbp_complete', 'dbp_nativename', 'dbp_height']

    if match.group(0).strip().lower() in NO_REPLACE_PURE or match.group(0).strip().lower() in NO_REPLACE_INTERM:
        return f' {match.group(0)} '

    prefix = match.group(0)[:3]
    if prefix not in PLACEHOLDERS:
        raise ValueError(f"UNKNOWN PREFIX: {prefix}")

    return f' {PLACEHOLDERS[prefix]} '