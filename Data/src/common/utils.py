# general utils

from typing import List, Tuple
import unicodedata

from common.consts import CAMEL_CASE_SPLIT_RE, REPLACEMENTS, RESOURCE_ABBRV, RESOURCE_TYPE, URI_SHORTENERS

def unicodeToAscii(s):
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )


def extract_alt_name(resource_type, uri_name):
    if resource_type == RESOURCE_TYPE or resource_type == RESOURCE_ABBRV:
        # underscores as space, no keep parentheses
        alt_name = uri_name.replace('_', ' ')
        alt_name = alt_name.split('(')[0]
        return alt_name.strip()

    else:
        alt_name = CAMEL_CASE_SPLIT_RE.findall(uri_name)
        return ' '.join(alt_name)


def gen_beg_end(n: int) -> List[Tuple[int, int]]:
    all_idx = []

    for i in range(n):
        for j in range(i + 1, n):
            all_idx.append({
                'beg': i,
                'end': j,
                'len': j-i
            })

    return [(i['beg'], i['end']) for i in sorted(all_idx, key=lambda d: d['len'], reverse=True)]


def get_pure_sparql_from_interm(interm_sparql: str) -> str:
  sparql = interm_sparql
  for r in REPLACEMENTS[:-3]:
      original = r[0]
      encoding = r[-1]
      sparql = sparql.replace(encoding, original)
      stripped_encoding = str.strip(encoding)
      sparql = sparql.replace(stripped_encoding, original)
  return sparql


def reduce_uri(uri):
    for r in URI_SHORTENERS:
        uri = uri.replace(r['match'], r['pure_sparql'])

    return uri