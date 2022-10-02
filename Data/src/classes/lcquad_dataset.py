import json
import re
from typing import Dict, List, Optional, Set, Tuple, cast, Union
from common.consts import GET_RESOURCES_PURE_SPARQL_RE, RE_TEMPLATE_EXCLUDE_SPECIFIC_RESOURCES, SPARQL_TYPE
from common.utils import reduce_uri
from classes.dataset import Dataset
from classes.entry import Entry, Flags, Query, Question
from common.re_callbacks import escape_uri_for_regex, convert_to_interm_sparql_except_resources, encode_resources_in_interm_sparql, lowercase_except_resources, encode_resources_in_pure_sparql, replace_resource_with_uri

def correct_resources_tags(resources_tags: List[str], template_id: Union[str, int], n_resources: int) -> List[str]:
    if type(template_id) is not int:
        print("Templates do not seem to be lcquad format, no resources tags to correct")
        return resources_tags

    if (template_id == 7 or template_id == 307) and n_resources == 3:
        resources_tags = resources_tags[1:]

    elif (template_id == 308) and n_resources == 4:
        resources_tags = resources_tags[:]
        resources_tags.pop(3)

    elif (template_id == 402) and n_resources == 2:
        resources_tags = resources_tags[:-1]

    elif (template_id == 305) and n_resources == 3:
        resources_tags = resources_tags[:]
        resources_tags.pop(3)

    elif (template_id == 5) and n_resources == 3:
        resources_tags = resources_tags[:]
        resources_tags.pop(3)

    elif (template_id == 105) and n_resources == 3:
        resources_tags = resources_tags[:]
        resources_tags.pop(3)

    return resources_tags


def correct_uri_question(match: re.Match) -> str:
    question = list(match.group(0))

    for g in range(len(match.groups()), 0, -1):
        span = match.span(g)
        to_replace = ''.join(question[span[0]:span[1]])
        to_replace = to_replace.replace("'s", " 's ")
        to_replace = to_replace.replace(",", "")
        to_replace = to_replace.replace('\"', "")
        question[span[0]:span[1]] = list(to_replace)

    return ''.join(question)


class LCQUADDataset(Dataset):

    RE_EVERYTHING_EXCEPT_RESOURCES = re.compile(
        "(^.*?<|>.*?<|>.*?$)", flags=re.IGNORECASE)
    RE_ONLY_RESOURCES = re.compile("(<.*?>)", flags=re.IGNORECASE)

    # Replacement flags order: (dbr, dbp, dbc, dbo)
    def __init__(self, train_data_path: Optional[str] = None, test_data_path: Optional[str] = None): # uri_replacement_flags: Tuple[bool, bool, bool, bool] = (False, False, False, False)):
        super().__init__()
        self.train_data_path = train_data_path
        self.test_data_path = test_data_path
        # self.uri_replacement_flags = uri_replacement_flags

        if self.train_data_path is not None and self.test_data_path is not None:
            self.load()
            self.complete_dataset()
            # optional - untag the elements that are not present in both the question and answer bcs the model wont be able to copy them in all cases
            # self.untag_elems_not_predictable()

    def load(self, train_data_path: Optional[str] = None, test_data_path: Optional[str] = None) -> None:

        if train_data_path is None:
            if self.train_data_path is not None:
                train_data_path = self.train_data_path
            else:
                raise ValueError("Missing train data path")

        if test_data_path is None:
            if self.test_data_path is not None:
                test_data_path = self.test_data_path
            else:
                raise ValueError("Missing test data path")

        with open(train_data_path, 'r', encoding='utf-8') as f:
            lcquad_train = json.load(f)

        for entry in lcquad_train:
            entry['original_set'] = 'train'
            entry['set'] = 'train'

        with open(test_data_path, 'r', encoding='utf-8') as f:
            lcquad_test = json.load(f)

        for i, entry in enumerate(lcquad_test):
            entry['original_set'] = 'test'
            entry['set'] = 'test' if i % 2 == 0 else 'valid'

        lcquad = lcquad_train + lcquad_test

        for json_entry in lcquad:
            new_entry = Entry(
                id_val=json_entry['_id'],
                original_data_val={
                'lcquad': {
                               'corrected_question': json_entry['corrected_question'],
                               'intermediary_question': json_entry['intermediary_question'],
                               'sparql_query': json_entry['sparql_query'],
                               'set': json_entry['original_set']
                    }
                },
                template_id_val=json_entry['sparql_template_id'],
                train_test_valid_set_val=json_entry['set'])
            self.entries.append(new_entry)

    def load_tntspa(self, tntspa_train_paths: Tuple[str, str], tntspa_test_paths: Tuple[str, str]):
        with open(tntspa_train_paths[0], 'r', encoding='utf-8') as f:
            train_data_nl = f.read().splitlines()

        with open(tntspa_train_paths[1], 'r', encoding='utf-8') as f:
            train_data_sp = f.read().splitlines()

        assert len(train_data_nl) == len(train_data_sp)

        for id, (nl, sparql) in enumerate(zip(train_data_nl, train_data_sp)):
            self.entries.append(Entry(
                id_val=id,
                question_val=Question(question=nl),
                query_val=Query(interm_sparql=sparql),
                train_test_valid_set_val='train'
            ))

        with open(tntspa_test_paths[0], 'r', encoding='utf-8') as f:
            test_data_nl = f.read().splitlines()

        with open(tntspa_test_paths[1], 'r', encoding='utf-8') as f:
            test_data_sp = f.read().splitlines()

        assert len(test_data_nl) == len(test_data_sp)

        for id, (nl, sparql) in enumerate(zip(test_data_nl, test_data_sp)):
            self.entries.append(Entry(
                id_val=id+len(train_data_nl),
                question_val=Question(question=nl),
                query_val=Query(interm_sparql=sparql),
                train_test_valid_set_val='test'
            ))

    def correct_template_id(self, template_id: int) -> int:
        if template_id == 605:
            template_id = 305

        elif template_id == 906:
            template_id = 306

        elif template_id == 601:
            template_id = 301

        return template_id

    def generate_pure_sparql(self, pure_lcquad_sparql: str) -> str:
        sparql = pure_lcquad_sparql.replace(
            f'<{SPARQL_TYPE}>', 'rdf:type')
        sparql = self.RE_EVERYTHING_EXCEPT_RESOURCES.sub(
            lowercase_except_resources, sparql)
        sparql = self.RE_ONLY_RESOURCES.sub(
            encode_resources_in_pure_sparql, sparql)
        sparql = sparql.replace('{', ' { ')
        sparql = sparql.strip()
        return re.sub('\s+', ' ', sparql)

    def generate_interm_sparql(self, pure_lcquad_sparql: str, keep_uris: bool, repl_flags: Flags = None) -> str:
        sparql = pure_lcquad_sparql.replace(
            f'<{SPARQL_TYPE}>', 'rdf_type')
        sparql = self.RE_EVERYTHING_EXCEPT_RESOURCES.sub(
            convert_to_interm_sparql_except_resources, sparql)
        sparql = self.RE_ONLY_RESOURCES.sub(
            lambda m: encode_resources_in_interm_sparql(m, keep_uris, repl_flags), sparql)

        sparql = sparql.replace('}', ' } ')
        sparql = sparql.replace('{', ' { ')
        sparql = sparql.strip()
        return re.sub('\s+', ' ', sparql)

    def _get_untagged_question(self, entry: Entry) -> str:
        question = self.correct_question(
            entry.get_from_original_data('lcquad', 'intermediary_question'))

        question = question.replace("'s", " 's ")
        question = question.replace(",", " , ")

        question = question.replace('<', '')
        question = question.replace('>', '')

        question = re.sub('\s+', ' ', question)

        return question

    def _tag_templated_question(self, entry: Entry, template, repl_flags: Flags) -> str:
        question = self.correct_question(
                entry.get_from_original_data('lcquad', 'intermediary_question'))
    
        if entry.template_id == 2:
            question = re.sub('(what|who) (is|are) the <(.*?)> of (.*?) \?', r"\1 \2 the <\3> of <\4> ?", question)

        question = question.replace("'s", " 's ")
        question = question.replace(",", " , ")

        resources = LCQUADDataset.RE_ONLY_RESOURCES.findall(question)
        resources_tags = correct_resources_tags(template['resource_tags'], entry.template_id, len(resources))

        if entry.template_id == 2:
            resources_tags = ["%(e_in_to_e)s", "%(e_in)s"]

        assert len(resources_tags) == len(resources)

        resources_with_tags = list(zip(resources_tags, resources))

        uris: List[str] = LCQUADDataset.RE_ONLY_RESOURCES.findall(entry.get_from_original_data('lcquad', 'sparql_query'))
        uris = [uri[1:-1] for uri in uris]
        uris = [reduce_uri(u) for u in uris if u != SPARQL_TYPE]

        uris_tags: List[str] = LCQUADDataset.RE_ONLY_RESOURCES.findall(str(template['template']).replace('class', '<class>'))
        uris_tags = [uri[1:-1] for uri in uris_tags]
        assert len(uris_tags) == len(uris)

        uris_with_tags = list(zip(uris_tags, uris))
        uris_with_tags = [(tag, uri) for tag, uri in uris_with_tags if uri != 'dbp:type']


        types_no_replace: List[str] = []
        types_no_replace += ['dbr:'] if not repl_flags.dbr else []
        types_no_replace += ['dbp:'] if not repl_flags.dbp else []
        types_no_replace += ['dbc:'] if not repl_flags.dbc else []
        types_no_replace += ['dbo:'] if not repl_flags.dbo else []

        for r_tag, resource in resources_with_tags:
            for u_tag, uri in uris_with_tags:
                if r_tag == u_tag:
                    if not uri.startswith(tuple(types_no_replace)):
                        question = question.replace(resource.lower(), uri)
                    break

        question = question.replace('<', '')
        question = question.replace('>', '')
        question = re.sub('\s+', ' ', question)
        return question

    def tag_templated_questions(self, templates) -> None:
        for entry in self.entries:
            template = [t for t in templates if t['id'] == entry.template_id][0]
            entry.question.interm_question = self._get_untagged_question(entry)

            all_flags = Flags(True)
            entry.question.uri_question_all = self._tag_templated_question(entry, template, all_flags)

            resource_flags = Flags(dbr=True)
            entry.question.uri_question_only_resources = self._tag_templated_question(entry, template, resource_flags)

            no_resource_flags = Flags(True, dbr=False)
            entry.question.uri_question_rest_no_resources = self._tag_templated_question(entry, template, no_resource_flags)



    def complete_dataset(self) -> None:
        for entry in self.entries:
            entry.template_id = self.correct_template_id(int(entry.template_id))
            entry.question.question = self.correct_question(
                entry.get_from_original_data('lcquad','corrected_question'))
            entry.query.pure_sparql = self.generate_pure_sparql(
                entry.get_from_original_data('lcquad','sparql_query'))

            all_flags = Flags(True)
            entry.query.uri_interm_sparql_all = self.generate_interm_sparql(
                entry.get_from_original_data('lcquad','sparql_query'), keep_uris=True, repl_flags=all_flags)

            entry.query.uri_interm_sparql_only_resources = entry.query.uri_interm_sparql_all.replace('dbc:', 'dbc_').replace('dbo:', 'dbo_').replace('dbp:', 'dbp_')
            entry.query.uri_interm_sparql_rest_no_resources = entry.query.uri_interm_sparql_all.replace('dbr:', 'dbr_')

            entry.query.interm_sparql = self.generate_interm_sparql(
                entry.get_from_original_data('lcquad','sparql_query'), keep_uris=False)

    def fix_original_question(self, question: str) -> bytes:
        question = question.lower()
        question = question.replace(' ', '')
        question = question.replace("?'", '?')
        if question[-1] == '/':
            question = question[:-1] + '?'
        question = question.replace(
            'http://dbpedia.org/resource/werner_heisenberg', '?')
        question = question.replace('whihc', 'which')
        question = question.replace('"', '')
        return question.encode('ascii', 'ignore')

    def fix_ref_question(self, question: str) -> bytes:
        question = question.lower()
        question = question.replace(' ', '')
        return question.encode('ascii', 'ignore')

    def get_tntspa_split_dataset(self, reference_dataset: Dataset) -> Dataset:
        resplit_dataset = LCQUADDataset()
        original_entries = self.entries[:]

        id_to_pos = {entry._id: idx for idx, entry in enumerate(self.entries)}

        for ref_entry in reference_dataset.entries:
            for entry in original_entries:

                if ref_entry.question.question is None:
                    raise ValueError("No reference question!") # freak error - should not happen - if it does, check how you load tntspa

                if self.fix_original_question(entry.get_from_original_data('lcquad','corrected_question')) == self.fix_ref_question(ref_entry.question.question):
                    # we found the corresponding tntspa entry
                    original_data = self.entries[id_to_pos[entry._id]].original_data
                    original_data['tntspa'] = {
                        'question': ref_entry.question.question,
                        'interm_sparql': ref_entry.query.interm_sparql,
                        'set': ref_entry.ttv_set
                    }
                    self.entries[id_to_pos[entry._id]].original_data = original_data

                    original_entries.remove(entry)
                    break

        assert len(original_entries) == 500
        for entry in original_entries:
            original_data = self.entries[id_to_pos[entry._id]].original_data
            original_data['tntspa'] = {}
            original_data['tntspa']['set'] = 'valid'
            self.entries[id_to_pos[entry._id]].original_data = original_data

        return resplit_dataset

    def untag_entry(self, question: str, query: str) -> Tuple[str, Set[str]]:
        tags = ['dbr:', 'dbo:', 'dbp:', 'dbc:']

        question_words = question.split()
        query_words = query.split()

        kb_elems_qst = set([w for w in question_words if w[:4] in tags])
        kb_elems_qry = set([w for w in query_words if w[:4] in tags]) 

        to_untag = kb_elems_qry - kb_elems_qst

        if len(to_untag) > 0:
            for i in range(len(query_words)):
                if query_words[i] in to_untag:
                    query_words[i] = query_words[i].replace(':', '_')

        return ' '.join(query_words), to_untag

    def untag_elems_not_predictable(self, untag_all=True) -> None:
        # ok so when building the vocabulary, the script (in models) will consider anything with a dbpedia uri tag (dbr:, dbc:, dbp:, dbo:) as being part of the extended vocab (to copy), and everything else (dbr_, dbc_, ...)
        # as part of the base vocab (to generate)

        # the problem is that if a question does not contain a tagged elem that a query does contain, the model will not be able to copy it
        # this function only handles when a query contains more resources than a question
        # ex:
        # question: What books were dbp:writtenBy dbr:Michel_Tremblay
        # query : select ?a where { ?a dbp:writtenBy dbr:Michel_Tremblay . ?a rdf:type dbo:Book . }

        # NOT the opposite case
        # ex:
        # question: What dbo:books were dbp:writtenBy dbr:Michel_Tremblay
        # query: select ?a where { ?a dbp:writtenBy dbr:Michel_Tremblay }

        # should not need to handle the opposite case anyways, because worst case it wont be copied BUT might be interesting to test with a neural tagging algorithm

        # if untag_all is False -> source vocab contains dbo_smth and extended contains dbo:smth (+ more things to copy)
        # if untag_all is True -> only source vocab contains dbo_smth (+ more examples of the same thing)

        untag_list_all = set()
        untag_list_ressources = set()
        untag_list_no_resources = set()

        for entry in self.entries:
            # all
            entry.query.uri_interm_sparql_all, to_untag_all_curr = self.untag_entry(entry.question.uri_question_all, entry.query.uri_interm_sparql_all)
            untag_list_all.update(to_untag_all_curr)

            # resources
            entry.query.uri_interm_sparql_only_resources, to_untag_res_curr = self.untag_entry(entry.question.uri_question_only_resources, entry.query.uri_interm_sparql_only_resources)
            untag_list_ressources.update(to_untag_res_curr)

            # rest
            entry.query.uri_interm_sparql_rest_no_resources, to_untag_rest_curr = self.untag_entry(entry.question.uri_question_rest_no_resources, entry.query.uri_interm_sparql_rest_no_resources)
            untag_list_no_resources.update(to_untag_rest_curr)

        if untag_all:
            for entry in self.entries:
                entry.query.uri_interm_sparql_all = ' '.join([w if w not in untag_list_all else w.replace(':', '_') for w in entry.query.uri_interm_sparql_all.split()])
                entry.query.uri_interm_sparql_only_resources = ' '.join([w if w not in untag_list_ressources else w.replace(':', '_') for w in entry.query.uri_interm_sparql_only_resources.split()])
                entry.query.uri_interm_sparql_rest_no_resources = ' '.join([w if w not in untag_list_no_resources else w.replace(':', '_') for w in entry.query.uri_interm_sparql_rest_no_resources.split()])

    # Attempt at building a word based tagging algorithm for corrected questions, not working
    def tag_questions_uri(self, resources_dict: Dict[str, List[str]]) -> None:
        for entry in self.entries:

            assert entry.query.uri_interm_sparql_all is not None # for mypy
            assert entry.question.question is not None # for mypy

            uri_question = entry.question.question
            uri_question = re.sub('(\(.*?\))', '', uri_question)

            uris = GET_RESOURCES_PURE_SPARQL_RE.findall(entry.query.uri_interm_sparql_all)
            uris = [reduce_uri(u) for u in uris if u != SPARQL_TYPE]

            regex = RE_TEMPLATE_EXCLUDE_SPECIFIC_RESOURCES.format(
                resources='|'.join([escape_uri_for_regex(uri) for uri in uris]))

            for uri in uris:
                uri_question = re.sub(regex, lambda m: replace_resource_with_uri(
                    m, resources_dict.get(uri,[]), uri), uri_question)


            regex = '(.*?)(?:{resources}|$)'.format(resources='|'.join([escape_uri_for_regex(uri) for uri in uris]))
            uri_question = re.sub(regex, correct_uri_question, uri_question)
            uri_question = re.sub('\s+', ' ', uri_question)

            # helps debugging
            # if uri_question.count('dbr:') + uri_question.count('dbc:') + uri_question.count('dbp:') + uri_question.count('dbo:') != len(uris):
            #     problem.append(entry.id)

            entry.question.uri_question_all = uri_question.strip()

