# utils to query dbpedia

import json
import argparse
from typing import Any, Dict
from SPARQLWrapper import SPARQLWrapper, JSON
from tqdm import tqdm

import ssl
from common.interm_sparql_to_pure_sparql import escape_query
ssl._create_default_https_context = ssl._create_unverified_context

ENDPOINT = "http://dbpedia.org/sparql"
GRAPH = "http://dbpedia.org"


def query_dbpedia(query: str) -> Dict[Any, Any]:
    sparql = SPARQLWrapper(ENDPOINT)
    sparql.setReturnFormat(JSON)

    sparql.setQuery(query)

    response: Dict[Any, Any] = sparql.query().convert()
    return response


def fetch_dbpedia_answers(json_dataset_path: str, force_all: bool = False) -> None:
    with open(json_dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    print("Running queries:")
    for entry in tqdm(dataset):
        if force_all or ("query_result" not in entry or entry["query_result"] is None):
            try:
                entry["query_result"] = query_dbpedia(
                    escape_query(entry["query"]["pure_sparql"]))

            except Exception as error:
                print(f"[ERROR] at query id {entry['_id']}:")
                print(error)

    with open(json_dataset_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch query results from dbpedia.")

    parser.add_argument("--in", dest='in_file', type=str, required=True,
                        help="path to the json file containing the dataset")

    parser.add_argument("--force_all", "-f", action="store_true", default=False,
                        help="wether or not to force refetch of ALL queries")

    args = parser.parse_args()
    fetch_dbpedia_answers(args.in_file, force_all=args.force_all)
