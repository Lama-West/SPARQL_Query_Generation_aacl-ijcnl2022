from __future__ import annotations
import copy
from typing import Any, Dict, Union, Optional
# mypy does NOT like this file


class Flags:
    def __init__(self, 
                 all_value: Optional[bool] = False,
                 *,
                 dbr: bool = None,
                 dbp: bool = None,
                 dbc: bool = None,
                 dbo: bool = None,
                 dct: bool = None,
                 georss: bool = None,
                 geo: bool = None):

            self.dbr = dbr if dbr is not None else all_value
            self.dbp = dbp if dbp is not None else all_value
            self.dbc = dbc if dbc is not None else all_value
            self.dbo = dbo if dbo is not None else all_value
            self.dct = dct if dct is not None else all_value
            self.georss = georss if georss is not None else all_value
            self.geo = geo if geo is not None else all_value

class Question:
    def __init__(self, *, question: Optional[str] = None, interm_question: Optional[str] = None, uri_question_only_resources: Optional[str] = None, uri_question_rest_no_resources: Optional[str] = None, uri_question_all: Optional[str] = None):
        self.question = question
        self.interm_question = interm_question
        self.uri_question_only_resources = uri_question_only_resources
        self.uri_question_rest_no_resources = uri_question_rest_no_resources
        self.uri_question_all = uri_question_all

    def from_json(self, data: Dict[str, str]):
        if 'question' in data:
            self.question = data['question']

        if 'interm_question' in data:
            self.interm_question = data['interm_question']

        if 'uri_question_only_resources' in data:
            self.uri_question_only_resources = data['uri_question_only_resources']

        if 'uri_question_rest_no_resources' in data:
            self.uri_question_rest_no_resources = data['uri_question_rest_no_resources']

        if 'uri_question_all' in data:
            self.uri_question_all = data['uri_question_all']

    @property
    def json(self):
        out_dict = {
            'question': self.question,
            'interm_question': self.interm_question,
            'uri_question_only_resources': self.uri_question_only_resources,
            'uri_question_rest_no_resources': self.uri_question_rest_no_resources,
            'uri_question_all': self.uri_question_all
        }

        return {key: val for key, val in out_dict.items() if val}


class Query:
    def __init__(self, *, interm_sparql: Optional[str] = None, uri_interm_sparql_only_resources: Optional[str] = None, uri_interm_sparql_rest_no_resources: Optional[str] = None, uri_interm_sparql_all: Optional[str] = None, pure_sparql: Optional[str] = None):
        self.interm_sparql = interm_sparql
        self.uri_interm_sparql_only_resources = uri_interm_sparql_only_resources
        self.uri_interm_sparql_rest_no_resources = uri_interm_sparql_rest_no_resources
        self.uri_interm_sparql_all = uri_interm_sparql_all
        self.pure_sparql = pure_sparql

    def from_json(self, data: Dict[str, str]):
        if 'interm_sparql' in data:
            self.interm_sparql = data['interm_sparql']

        if 'uri_interm_sparql_only_resources' in data:
            self.uri_interm_sparql_only_resources = data['uri_interm_sparql_only_resources']

        if 'uri_interm_sparql_rest_no_resources' in data:
            self.uri_interm_sparql_rest_no_resources = data['uri_interm_sparql_rest_no_resources']

        if 'uri_interm_sparql_all' in data:
            self.uri_interm_sparql_all = data['uri_interm_sparql_all']
        
        if 'pure_sparql' in data:
            self.uri_question_all = data['pure_sparql']

    @property
    def json(self):
        out_dict = {
            'interm_sparql': self.interm_sparql,
            'uri_interm_sparql_only_resources': self.uri_interm_sparql_only_resources,
            'uri_interm_sparql_rest_no_resources': self.uri_interm_sparql_rest_no_resources,
            'uri_interm_sparql_all': self.uri_interm_sparql_all,
            'pure_sparql': self.pure_sparql
        }

        return {key: val for key, val in out_dict.items() if val}


class Entry:

    def __init__(self, *,
                 id_val: Optional[Union[str, int]] = None,
                 template_id_val: Optional[int] = None,
                 question_val: Optional[Question] = None,
                 query_val: Optional[Query] = None,
                 train_test_valid_set_val: Optional[str] = None,
                 original_data_val: Optional[Dict[str, Any]] = None,
                 dbpedia_result_val: Optional[Dict] = None):

        self._id = str(id_val)
        self._template_id = template_id_val

        if question_val is None:
            self._question = Question()
        else:
            self._question = question_val

        if query_val is None:
            self._query = Query()
        else:
            self._query = query_val

        self._ttv_set = train_test_valid_set_val
        self._original_data = original_data_val
        self._dbpedia_result = dbpedia_result_val

# region properties
    # id ---------------

    @property
    def id(self) -> str:
        if self._id is None:
            raise ValueError("Tried to access id but no value set")
        return self._id

    @id.setter
    def id(self, val: Union[str, int]):
        self._id = str(val)

    # template_id ---------------
    @property
    def template_id(self) -> Union[str, int]:
        if self._template_id is None:
            raise ValueError("Tried to access template_id but no value set")
        return self._template_id

    @template_id.setter
    def template_id(self, val: Union[str, int]):
        self._template_id = val

    # question ---------------
    @property
    def question(self) -> Question:
        if self._question is None:
            raise ValueError("Tried to access question but no value set")
        return self._question

    @question.setter
    def question(self, val: Question):
        self._question = val

    # query ---------------
    @property
    def query(self) -> Query:
        if self._query is None:
            raise ValueError("Tried to access query but no value set")
        return self._query

    @query.setter
    def query(self, val: Query):
        self._query = val

    # ttv_set ---------------
    @property
    def ttv_set(self) -> str:
        if self._ttv_set is None:
            raise ValueError("Tried to access ttv_set but no value set")
        return self._ttv_set

    @ttv_set.setter
    def ttv_set(self, val: str):
        self._ttv_set = val

    # original_data  ---------------
    @property
    def original_data(self) -> Dict[Any, Any]:
        if self._original_data is None:
            raise ValueError("Tried to access original_data but no value set")
        return self._original_data

    @original_data.setter
    def original_data(self, val: Dict[Any, Any]):
        self._original_data = val

    # dbpedia_result ---------------
    @property
    def dbpedia_result(self) -> Dict:
        if self._dbpedia_result is None:
            raise ValueError("Tried to access dbpedia_result but no value set")
        return self._dbpedia_result

    @dbpedia_result.setter
    def dbpedia_result(self, val: Dict):
        self._dbpedia_result = val

    # json --------------------
    @property
    def json(self) -> Dict[str, Union[str, int, Dict[Any, Any]]]:

        if not self.contains_minimum_information():
            print("Missing required information for complete dataset")

        encoded_original_data = self._original_data

        if self._original_data is not None:
            encoded_original_data = copy.deepcopy(self._original_data)

            for key in encoded_original_data:
                if type(encoded_original_data[key]) is Question or type(encoded_original_data[key]) is Query:
                    encoded_original_data[key] = encoded_original_data[key].json

        out_dict: Dict[str, Union[None, str, int, Dict[Any, Any]]] = {
            '_id': self.id,  # REQUIRED
            'template_id': self._template_id,
            'question': self.question.json, # REQUIRED
            'query': self.query.json,  # REQUIRED
            'set': self.ttv_set,  # REQUIRED
            'original_data': encoded_original_data,
            'dbpedia_result': self._dbpedia_result
        }

        return {key: val for key, val in out_dict.items() if val}
# endregion

    def get_from_original_data(self, key: str, subkey: Optional[str] = None) -> Any:
        if key not in self.original_data:
            raise ValueError(f'{key} not in original data')

        if subkey is None:
            return self.original_data[key]

        elif subkey not in self.original_data[key]:
            raise ValueError(f'{subkey} not in original_data[{key}]')\

        return self.original_data[key][subkey]

    def contains_minimum_information(self) -> bool:
        if self._id is None or self._question is None \
                or self._query is None or self._ttv_set is None:
            return False

        return True

    def from_json(self, json_data: Dict[str, Union[str, int, Dict[Any, Any]]]):
        if '_id' not in json_data:  # REQUIRED
            raise ValueError("Missing _id in json data")
        elif not isinstance(json_data['_id'], int) and not isinstance(json_data['_id'], str):
            raise ValueError("_id should be a str or an int")
        else:
            self.id = str(json_data['_id'])

        if 'template_id' in json_data:
            if not isinstance(json_data['template_id'], int) and not isinstance(json_data['template_id'], str):
                raise ValueError("template_id should be a str or an int")
            else:
                self.template_id = json_data['template_id']

        if 'question' not in json_data:  # REQUIRED
            raise ValueError("Missing question in json data")
        elif not isinstance(json_data['question'], dict):
            raise ValueError("question should be a dict")
        else:
            qst = Question()
            qst.from_json(json_data['question'])
            self.question = qst

        if 'query' not in json_data:  # REQUIRED
            raise ValueError("Missing query in json data")
        elif not isinstance(json_data['query'], dict):
            raise ValueError("query should be a dict")
        else:
            qry = Query()
            qry.from_json(json_data['query'])
            self.query = qry

        if 'set' not in json_data:  # REQUIRED
            raise ValueError("Missing set in json data")
        elif not isinstance(json_data['set'], str):
            raise ValueError("set should be a str")
        else:
            self.ttv_set = json_data['set']

        if 'original_data' in json_data:
            if not isinstance(json_data['original_data'], dict):
                raise ValueError("original_data should be a dict")
            else:
                self.original_data = json_data['original_data']

        if 'dbpedia_result' in json_data:
            if not isinstance(json_data['dbpedia_result'], dict):
                raise ValueError("dbpedia_result should be a dict")
            else:
                self.dbpedia_result = json_data['dbpedia_result']
