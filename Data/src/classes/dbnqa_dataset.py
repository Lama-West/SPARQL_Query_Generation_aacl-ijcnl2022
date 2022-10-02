import math
import re
import random
from typing import Dict, List, Optional, Tuple

from tqdm import tqdm
from typer import Option

from classes.dataset import Dataset
from classes.entry import Entry

from common.consts import GET_RESOURCES_INTERM_SPARQL_RE, GET_RESOURCES_PURE_SPARQL_RE, RE_TEMPLATE_EXCLUDE_SPECIFIC_RESOURCES
from common.interm_sparql_to_pure_sparql import interm_sparql_to_pure_sparql
from common.re_callbacks import escape_uri_for_regex, replace_resource_with_uri


class DBNQADataset(Dataset):

    def __init__(self, nl_data_path: str, sparql_data_path: str, subset: Optional[int] = None, train_ratio: float = 0.8, valid_ratio: float = 0.1, test_ratio: float = 0.1):
        super().__init__(train_ratio, valid_ratio, test_ratio)
        self.nl_data_path = nl_data_path
        self.sparql_data_path = sparql_data_path

        if self.nl_data_path is not None and self.sparql_data_path is not None:
            self.load(subset=subset)
            self.complete_dataset()
            self.split_train_test_val()

    def load(self, nl_data_path: Optional[str] = None, sparql_data_path: Optional[str] = None, subset: Optional[int] = None) -> None:
        if nl_data_path is None:
            if self.nl_data_path is not None:
                nl_data_path = self.nl_data_path
            else:
                raise ValueError("Missing nl data path")

        if sparql_data_path is None:
            if self.sparql_data_path is not None:
                sparql_data_path = self.sparql_data_path
            else:
                raise ValueError("Missing sparql data path")

        with open(nl_data_path, 'r', encoding='utf-8') as f:
            nl_data = f.read().splitlines()

        with open(sparql_data_path, 'r', encoding='utf-8') as f:
            sparql_data = f.read().splitlines()

        if not(len(nl_data) == len(sparql_data)):
            raise ValueError(
                "Data files do not contain same number of entries")

        for id, (nl, sparql) in enumerate(zip(nl_data, sparql_data)):
            new_entry = Entry(
                id_val=id,
                original_data_val={
                    'question': nl,
                    'interm_sparql': sparql
                }
            )

            self.entries.append(new_entry)

        if subset is not None:
            self.entries = self.entries[:subset]

    def generate_uri_interm_sparql(self, interm_sparql: str, pure_sparql: str) -> str:
        entities_pure_sparql = GET_RESOURCES_PURE_SPARQL_RE.findall(
            pure_sparql)
        entities_interm_sparql = GET_RESOURCES_INTERM_SPARQL_RE.findall(
            interm_sparql)

        assert len(entities_pure_sparql) == len(entities_interm_sparql)

        entities_interm_sparql = [parts[0] for parts in entities_interm_sparql]

        interm_sparql_all = interm_sparql

        for pure, interm in zip(entities_pure_sparql, entities_interm_sparql):
            interm_sparql_all = interm_sparql_all.replace(interm, pure, 1)

        interm_sparql = re.sub('\s+', ' ', interm_sparql)
        interm_sparql = interm_sparql.strip()

        return interm_sparql_all

    def complete_dataset(self) -> None:
        for entry in tqdm(self.entries):
            entry.question.question = self.correct_question(
                entry.get_from_original_data('question'))
            entry.query.interm_sparql = self.correct_interm_sparql(
                entry.get_from_original_data('interm_sparql'))
            entry.query.pure_sparql = interm_sparql_to_pure_sparql(
                entry.query.interm_sparql)
            entry.query.uri_interm_sparql_all = self.generate_uri_interm_sparql(entry.query.interm_sparql, entry.query.pure_sparql)

            entry.query.uri_interm_sparql_only_resources = entry.query.uri_interm_sparql_all.replace('dbc:', 'dbc_').replace('dbo:', 'dbo_').replace('dbp:', 'dbp_')
            entry.query.uri_interm_sparql_rest_no_resources = entry.query.uri_interm_sparql_all.replace('dbr:', 'dbr_')

    # NOT WORKING AND UNUSED

    def tag_questions_uri(self, resources_dict: Dict[str, List[str]]) -> None:
        for entry in tqdm(self.entries):
            uris = GET_RESOURCES_PURE_SPARQL_RE.findall(
                entry.query.pure_sparql)
            uris = [uri[0] for uri in uris]

            regex = RE_TEMPLATE_EXCLUDE_SPECIFIC_RESOURCES.format(
                resources='|'.join([escape_uri_for_regex(uri) for uri in uris]))

            for uri in uris:
                uri_question = re.sub(regex, lambda m: replace_resource_with_uri(
                    m, resources_dict[uri], uri), entry.question.question)

            uri_question = re.sub('\s+', ' ', uri_question)
            entry.question.uri_question_all = uri_question.strip()
