# utils to help converting interm_sparql back to pure sparql

from typing import List
import re
from common.consts import CATCH_VAR_IN_RESOURCE_NAME_RE, GET_RESOURCES_PURE_SPARQL_RE, REPLACE_ORDER_BY_RE, REPLACEMENTS
import argparse
from tqdm import tqdm


def reverse_replacements(query: str) -> str:
    for r in REPLACEMENTS:
        original = r[0]
        encoding = r[-1]
        query = query.replace(encoding, original)
        stripped_encoding = str.strip(encoding)
        query = query.replace(stripped_encoding, original)

    return query


def escape_order_by(query: str) -> str:
    matches = REPLACE_ORDER_BY_RE.findall(query)

    if len(matches) == 0:
        return query

    matches = matches[0]

    if len(matches) > 3:
        raise ValueError(f"The query '{query}' has more than one order by!")

    if matches[1] == "_oba_":
        order_by = "ORDER BY ASC("
    elif matches[1] == "_obd_":
        order_by = "ORDER BY DESC("

    order_by_str = order_by + matches[2] + ")"
    query = query.replace(matches[0], order_by_str)

    return query


def remove_spaces_from_resources(match: re.Match) -> str:
    entity = match.group(0)
    entity = entity.replace(" ", "")
    entity = entity.replace("\\", "")
    entity = entity.replace(' attr_dot ', ".")
    entity = entity.replace(' attr_dot', ".")
    entity = entity.replace('attr_dot ', ".")
    entity = entity.replace('attr_dot', ".")
    return f" {entity} "


def add_var_in_resource_names(match: re.Match) -> str:
    return str(match.group(0).replace('?', 'var_'))


def interm_sparql_to_pure_sparql(interm_query: str):
    query = reverse_replacements(interm_query)
    query = escape_order_by(query)
    query = CATCH_VAR_IN_RESOURCE_NAME_RE.sub(add_var_in_resource_names, query)
    query = query.replace("where{", "where {")
    query = query.replace("}", " } ")
    query = query.replace("FILTER", "filter")
    query = query.replace("COUNT", "count")
    query = query.replace("UNION", "union")

    query = GET_RESOURCES_PURE_SPARQL_RE.sub(remove_spaces_from_resources, query)

    query = query.replace("dbp:length", " dbp:length ")
    query = re.sub(" ?%3F", "?", query)
    query = re.sub("\s+", " ", query)
    query = query.strip()
    return query


def generate_pure_sparql(interm_sparql: List[str]) -> List[str]:
    pure_sparql = []

    for interm_query in tqdm(interm_sparql):
        query = interm_sparql_to_pure_sparql(interm_query)
        pure_sparql.append(query)
    
    return pure_sparql


def escape_parentheses_in_entities(match: re.Match) -> str:
    resource: str = match.group(0)
    resource = resource.replace('(', '\\(')
    resource = resource.replace(')', '\\)')
    return resource


def escape_parentheses(query: str) -> str:
    query = GET_RESOURCES_PURE_SPARQL_RE.sub(escape_parentheses_in_entities, query)
    return query


def escape_ampersands(query: str) -> str:
    amp = query.find('&')
    while amp > 0:
        if query[amp - 1] != '&' and query[amp + 1] != '&':
            query = query[:amp] + '\\' + query[amp:]
        amp = query.find('&', amp + 2)
    return query


def escape_dots_in_resources(match:re.Match) -> str:
    full_match: str = match.group(0)
    return full_match.replace('.', '\\.')


def escape_dots(query: str) -> str:
    query = GET_RESOURCES_PURE_SPARQL_RE.sub(escape_dots_in_resources, query)
    return query


def escape_plus(query: str) -> str:
    idx = query.find('+')
    while idx > 0:
        query = query[:idx] + '\\' + query[idx:]
        idx = query.find('+', idx + 2)
    return query


def escape_star(query: str) -> str:
    idx = query.find('*')
    while idx > 0:
        query = query[:idx] + '\\' + query[idx:]
        idx = query.find('*', idx + 2)
    return query


def escape_query(query: str) -> str:
    query = escape_parentheses(query)
    query = escape_ampersands(query)
    query = escape_dots(query)
    query = escape_plus(query)
    # query = escape_star(query)
    query = escape_order_by(query)
    query = query.replace("'", "\\'")
    query = query.replace(",", "\\,")
    query = query.replace("!", "\\!")
    query = query.replace("/", "\\/")
    return query


def escape_for_querying(pure_sparql: List[str]) -> List[str]:
    escaped_sparql = []
    for query in tqdm(pure_sparql):
        escaped_sparql.append(escape_query(query))
    return escaped_sparql


def convert_to_pure_sparql(in_path_intem_sparql: str, out_path_pure_sparql: str, escape: bool = False) -> None:
    interm_sparql = open(in_path_intem_sparql, 'r',
                         encoding="utf-8").read().strip().split('\n')

    pure_sparql = generate_pure_sparql(interm_sparql)

    if escape:
        pure_sparql = escape_for_querying(pure_sparql)

    with open(out_path_pure_sparql, 'w', encoding="utf-8") as f:
        f.writelines('\n'.join(pure_sparql))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Convert interm sparql queries into pure sparql queries.")

    parser.add_argument("--in", dest='in_file', type=str, required=True,
                        help="path to the txt file containing intermediary sparql queries separated by newlines")

    parser.add_argument("--out", type=str, required=True,
                        help="path to the txt file containing converted pure sparql queries separated by newlines")

    parser.add_argument("--escape", "-e", action="store_true", default=False,
                        help="wether or not to escape the queries to make them runnable on dbpedia")

    args = parser.parse_args()
    convert_to_pure_sparql(args.in_file, args.out, escape=args.escape)
