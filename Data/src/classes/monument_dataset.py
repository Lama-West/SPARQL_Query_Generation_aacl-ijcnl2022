import json
import re
from typing import Dict, List, Optional, Tuple, Union

from classes.entry import Entry, Flags
from classes.dataset import Dataset
from common.consts import FIND_RESOURCES_BTW_ANGLE_BRACKETS_RE
from common.interm_sparql_to_pure_sparql import interm_sparql_to_pure_sparql
from common.re_callbacks import insert_resources


class MonumentDataset(Dataset):
    def __init__(self, nl_data_path: Optional[str] = None, sparql_data_path: Optional[str] = None, templates_path: Optional[str] = None, assign_templates: bool = True):
        super().__init__()
        if nl_data_path is not None and sparql_data_path is not None:
            self.load(nl_data_path=nl_data_path,
                      sparql_data_path=sparql_data_path, templates_path=templates_path)
            self.correct_dataset()
            self.split_train_test_val()

            if templates_path is not None:
                self.complete_dataset(assign_templates)

    def load(self, nl_data_path: Optional[str] = None, sparql_data_path: Optional[str] = None, templates_path: Optional[str] = None) -> None:
        if templates_path:
            self.load_templates(templates_path)
        else:
            print("[INFO] No template path provided, no templates loaded")

        if nl_data_path is None:
            raise ValueError("Missing nl data path")

        if sparql_data_path is None:
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

    def load_templates(self, templates_path: str) -> None:
        with open(templates_path, 'r', encoding='utf-8') as f:
            self.templates: List[Dict] = json.load(f)

    def get_template_id(self, entry: Entry) -> Union[int, str]:
        t_id: Union[str, int, None] = None

        for t in self.templates:
            if re.match(t['interm_sparql_regex'], entry.query.interm_sparql):
                if re.match(t['question_regex'], entry.question.question):
                    t_id = t['_id']
                    exact_match_found = True
                    break

        if t_id is None or not exact_match_found:
            raise ValueError(
                f"Incomplete templates, no exact match found for {entry.query.interm_sparql}")

        return t_id

    def get_template_by_id(self, id: Union[int, str]) -> Dict:
        for t in self.templates:
            if t['_id'] == id:
                return t

        raise ValueError(f'Template id {id} not found')

    def generate_uri_interm_sparql(self, entry: Entry) -> Tuple[str, str, str]:
        template = self.get_template_by_id(entry.template_id)

        entities_pure_sparql = re.match(
            template['pure_sparql_regex'], entry.query.pure_sparql, flags=re.IGNORECASE)

        if entities_pure_sparql is None:
            raise ValueError(f"Wrong template id for entry {entry.id}")

        list_entities_pure_sparql = list(entities_pure_sparql.groups())

        placeholders = FIND_RESOURCES_BTW_ANGLE_BRACKETS_RE.findall(
            template['interm_sparql_template'])

        only_resources_interm_sparql = str(template['interm_sparql_template'])
        all_uri_interm_sparql = str(template['uri_interm_sparql_template'])
        rest_no_resources_interm_sparql = str(
            template['uri_interm_sparql_template'])

        assert len(placeholders) == len(list_entities_pure_sparql)

        for pl, ent in zip(placeholders, list_entities_pure_sparql):
            only_resources_interm_sparql = only_resources_interm_sparql.replace(
                f'<{pl}>', ent.strip())
            all_uri_interm_sparql = all_uri_interm_sparql.replace(
                f'<{pl}>', ent.strip())
            rest_no_resources_interm_sparql = rest_no_resources_interm_sparql.replace(
                f'<{pl}>', ent.strip().replace(':', '_'))

        # uri_interm_sparql: str = re.sub(template['interm_sparql_regex'], lambda m: insert_resources(m, list_entities_pure_sparql), entry.query.interm_sparql, flags=re.IGNORECASE)
        only_resources_interm_sparql = re.sub(
            '\s+', ' ', only_resources_interm_sparql)
        only_resources_interm_sparql = only_resources_interm_sparql.strip()

        rest_no_resources_interm_sparql = re.sub(
            '\s+', ' ', rest_no_resources_interm_sparql)
        rest_no_resources_interm_sparql = rest_no_resources_interm_sparql.strip()

        all_uri_interm_sparql = re.sub('\s+', ' ', all_uri_interm_sparql)
        all_uri_interm_sparql = all_uri_interm_sparql.strip()

        return all_uri_interm_sparql, only_resources_interm_sparql, rest_no_resources_interm_sparql

    def generate_uri_question(self, entry: Entry) -> Tuple[str, str, str]:
        template = self.get_template_by_id(entry.template_id)

        # uris
        order_sparql = FIND_RESOURCES_BTW_ANGLE_BRACKETS_RE.findall(
            template['interm_sparql_template'])

        entities_pure_sparql = re.match(
            template['pure_sparql_regex'],  entry.query.pure_sparql, flags=re.IGNORECASE)

        # labels
        order_question = FIND_RESOURCES_BTW_ANGLE_BRACKETS_RE.findall(
            template['question_template'])

        labels = re.match(
            template['question_regex'], entry.question.question, flags=re.IGNORECASE)

        # check if right template
        if entities_pure_sparql is None or labels is None:
            raise ValueError(f"Wrong template id for entry {entry.id}")

        # uri dict
        list_entities_pure_sparql = entities_pure_sparql.groups()
        entities_dict_sparql = {order: uri for order, uri in zip(
            order_sparql, list_entities_pure_sparql)}

        # labels dict
        labels = labels.groups()
        labels_dict = {order: label for order, label in zip(
            order_question, labels)}

        placeholders = FIND_RESOURCES_BTW_ANGLE_BRACKETS_RE.findall(
            template['question_template'])

        only_resources_question = str(template['question_template'])
        rest_no_resources_question = str(template['uri_question_template'])
        all_uri_question = str(template['uri_question_template'])

        assert len(placeholders) == len(entities_dict_sparql.keys())

        for pl in placeholders:
            only_resources_question = only_resources_question.replace(
                f'<{pl}>', entities_dict_sparql[pl].strip())
            rest_no_resources_question = rest_no_resources_question.replace(
                f'<{pl}>', labels_dict[pl].strip())
            all_uri_question = all_uri_question.replace(
                f'<{pl}>', entities_dict_sparql[pl].strip())

        only_resources_question = re.sub('\s+', ' ', only_resources_question)
        rest_no_resources_question = re.sub('\s+', ' ', rest_no_resources_question)
        all_uri_question = re.sub('\s+', ' ', all_uri_question)

        return all_uri_question.strip(), only_resources_question.strip(), rest_no_resources_question.strip()

    def correct_dataset(self) -> None:
        for entry in self.entries:
            entry.question.question = self.correct_question(
                entry.get_from_original_data('question'))
            entry.query.interm_sparql = self.correct_interm_sparql(
                entry.get_from_original_data('interm_sparql'))
            entry.query.pure_sparql = interm_sparql_to_pure_sparql(
                entry.query.interm_sparql)

    def complete_dataset(self, assign_templates: bool = False) -> None:
        for entry in self.entries:
            if assign_templates:
                entry.template_id = self.get_template_id(entry)

            entry.query.uri_interm_sparql_all, entry.query.uri_interm_sparql_only_resources, entry.query.uri_interm_sparql_rest_no_resources = self.generate_uri_interm_sparql(
                entry)
            entry.question.uri_question_all, entry.question.uri_question_only_resources, entry.question.uri_question_rest_no_resources = self.generate_uri_question(
                entry)
