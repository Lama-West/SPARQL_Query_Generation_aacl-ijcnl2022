from abc import ABC, abstractmethod
import math
import random
import re
from typing import Dict, List, Union

import json

from tqdm import tqdm
from classes.entry import Entry

from common.consts import GET_RESOURCES_INTERM_SPARQL_RE, INSERT_SPACES_MATH_RE, REPLACE_FILTER_PAR_RE, REPLACE_QUOTES_RE, REPLACE_REST_PAR_RE
from common.re_callbacks import correct_sep_dots, insert_spaces_math, correct_parentheses_interm_sparql, replace_quotes


class Dataset(ABC):
    def __init__(self, train_ratio: float = 0.8, valid_ratio: float = 0.1, test_ratio: float = 0.1):
        self.entries: List[Entry] = []

        self.train_ratio = train_ratio
        self.valid_ratio = valid_ratio
        self.test_ratio = test_ratio

        assert train_ratio + valid_ratio + test_ratio == 1

    @property
    def json(self) -> List[Dict]:
        return [entry.json for entry in self.entries]

    @abstractmethod
    def load(self):
        pass

    def save(self, out_path: str) -> None:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(self.json, f, indent=4)

    def correct_question(self, question: str) -> str:
        # TODO: maybe a lib to fix typos?
        try:
            og_question = question
            question = question.lower().strip()
            question = question.replace('wasthe', 'was the')
            question = question.replace('monthyl', 'monthly')
            question = question.replace('grevais', 'gervais')
            question = question.replace('joesph', 'joseph')
            question = question.replace('palce', 'place')
            question = question.replace('whihc', 'which')
            question = question.replace('whci', 'which')
            question = question.replace(' od ', ' of ')
            question = question.replace('emplyer', 'employer')
            question = question.replace('ispychess', 'is pychess')
            question = question.replace("compnay", "company")
            question = question.replace("comapny", "company")
            question = question.replace("genere", "genre")
            question = question.replace("palce", "place")
            question = question.replace("herny ford", "henry ford")
            question = question.replace(" aldo ", " also ")
            question = question.replace(" aldo ", " also ")
            question = question.replace(" form ", " from ")
            question = question.replace(" of from ", " of form ")
            question = question.replace(" awrds ", " awards ")
            question = question.replace(" awardwinners ", " award winners ")
            question = question.replace(" castillo ", " callisto")
            question = question.replace(" castillo ", " callisto")
            question = question.replace("rishkiesh", "rishikesh")
            question = question.replace("kriminalpolizie", "kriminalpolizei")
            question = question.replace("willian", "william")
            question = question.replace("ehtics", "ethics")
            question = question.replace("terrotory", "territory")
            question = question.replace("snaman", "sandman")
            question = question.replace("neverwher", "neverwhere")
            question = question.replace("hopoer", "hooper")
            question = question.replace("ho0lder", "holder")
            question = question.replace("marvo", "mavro")
            question = question.replace("micheal", "michael")
            question = question.replace("brandenton", "bradenton")
            question = question.replace("fraiser", "frasier")
            question = question.replace(" firt ", " first ")
            question = question.replace(" asnorth ", " as north ")
            question = question.replace(" electoin ", " election ")

            question = question.replace('\\"', ' \\" ')

            question = question.replace("< ", "")
            question = question.replace(
                'http://dbpedia.org/resource/werner_heisenberg', '')

            if question[0] == '?':
                question = question[1:] + '?'

            question = question.replace(' jr ', ' jr. ')
            question = question.replace(' sr ', ' sr. ')
            question = re.sub('(?:\?)(.*)', '', question)

            if question[-1] == '.':
                question = question[:-1] + '?'

            if question[-1] == '/':
                question = question[:-1] + '?'

            elif question[-2] == "?'":
                question = question[:-2] + '?'

            if question[-1] != '?':
                question = question + ' ? '

            question = question.replace('?', ' ? ')
            question = re.sub('\s+', ' ', question)
            question = question.strip()

        except Exception as e:
            print(e)
            print(og_question)
            print(question)

        return question

    def correct_interm_sparql(self, interm_sparql: str) -> str:
        interm_sparql = interm_sparql.replace('attr_open', ' par_open ')
        interm_sparql = interm_sparql.replace('attr_close', ' par_close ')

        interm_sparql = re.sub('\s+', ' ', interm_sparql)

        interm_sparql = interm_sparql.replace('var_uri.', 'var_uri sep_dot') #dbnqa
        interm_sparql = interm_sparql.replace('brack_open', ' brack_open ')
        interm_sparql = interm_sparql.replace('brack_close', ' brack_close ')
        interm_sparql = interm_sparql.replace('dbp_length', ' dbp_length ')

        interm_sparql = REPLACE_FILTER_PAR_RE.sub(
            correct_parentheses_interm_sparql, interm_sparql)
        interm_sparql = REPLACE_REST_PAR_RE.sub(
            correct_parentheses_interm_sparql, interm_sparql)
        interm_sparql = REPLACE_QUOTES_RE.sub(replace_quotes, interm_sparql)
        interm_sparql = GET_RESOURCES_INTERM_SPARQL_RE.sub(
            correct_sep_dots, interm_sparql)
        interm_sparql = INSERT_SPACES_MATH_RE.sub(
            insert_spaces_math, interm_sparql)

        interm_sparql = interm_sparql.replace('FILTER', 'filter')
        interm_sparql = interm_sparql.replace('COUNT', 'count')
        interm_sparql = interm_sparql.replace('UNION', 'union')

        interm_sparql = interm_sparql.replace('%3F', '?')

        interm_sparql = re.sub('\s+', ' ', interm_sparql)
        interm_sparql = interm_sparql.strip()

        interm_sparql = interm_sparql.replace('par_open', 'attr_open')
        interm_sparql = interm_sparql.replace('par_close', 'attr_close')
        interm_sparql = interm_sparql.replace('sparql_open', 'par_open')
        interm_sparql = interm_sparql.replace('sparql_close', 'par_close')

        return interm_sparql

    def split_train_test_val(self, train_ratio: float = None, valid_ratio: float = None, test_ratio: float = None):
        if train_ratio is None:
            if self.train_ratio:
                train_ratio = self.train_ratio
            else:
                raise ValueError("Please specify train ratio")

        if valid_ratio is None:
            if self.valid_ratio:
                valid_ratio = self.valid_ratio
            else:
                raise ValueError("Please specify valid ratio")

        if test_ratio is None:
            if self.test_ratio:
                test_ratio = self.test_ratio
            else:
                raise ValueError("Please specify test ratio")

        assert train_ratio + test_ratio + valid_ratio == 1

        random.shuffle(self.entries)

        start_idx_validation = math.floor(len(self.entries) * train_ratio) + 1
        start_idx_test = math.floor(
            len(self.entries) * (train_ratio + valid_ratio)) + 1

        for i in range(len(self.entries)):
            if i < start_idx_validation:
                self.entries[i].ttv_set = 'train'
            elif start_idx_validation <= i < start_idx_test:
                self.entries[i].ttv_set = 'valid'
            else:
                self.entries[i].ttv_set = 'test'

    def get_entry_at_id(self, id: Union[str, int]) -> Entry:
        for entry in self.entries:
            if id == entry.id:
                return entry

        raise ValueError(f'Entry with id {id} not found in dataset')
