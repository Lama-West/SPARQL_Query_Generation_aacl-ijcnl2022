# When calculating the BLEU score, the colab notebooks generate an "error_report.json" file that contains all the translations for
# the test set. Admittedly the name "error report" is a bit misleading, but this script calculates the answer accuracy score of a test set.
# It also calculate more specific metrics such as the accuracy per template it can compare the variations between two reports.

import argparse
import json
from typing import Dict, List
from torchtext.data.metrics import bleu_score

from tqdm import tqdm
from common.interm_sparql_to_pure_sparql import escape_query, interm_sparql_to_pure_sparql
from common.query_dbpedia import query_dbpedia

from Levenshtein import distance as levenshtein_distance


def generate_pure_sparql(interm_sparql: str) -> str:
    pure_sparql: str = interm_sparql_to_pure_sparql(interm_sparql)
    pure_sparql = escape_query(pure_sparql)
    pure_sparql = pure_sparql.replace(' var_b ', ' ?b ')
    pure_sparql = pure_sparql.replace('<', '')
    return pure_sparql.replace('>', '')


def generate_pure_sparql_for_report(partial_report: List[Dict[str, str]]) -> List[Dict[str, str]]:

    for id in range(len(partial_report)):
        partial_report[id]['pure_trg'] = generate_pure_sparql(partial_report[id]['trg'])
        partial_report[id]['pure_predicted']= generate_pure_sparql(partial_report[id]['predicted'])

    return partial_report


def query_dbpedia_for_report(complete_report: List[Dict[str, str]], predicted=False) -> List[Dict[str, str]]:
    dbpedia_key = 'predicted' if predicted else 'trg'
    pure_sparql_key = 'pure_predicted' if predicted else 'pure_trg'

    for entry in tqdm(complete_report):
        try:
            dbpedia_data = entry.get('dbpedia', {'predicted': {}, 'trg': {}})
            dbpedia_data[dbpedia_key]['query_result'] = query_dbpedia(entry[pure_sparql_key])
            dbpedia_data[dbpedia_key]['is_error'] = False
            entry['dbpedia'] = dbpedia_data

        except Exception as error:
            print(f"[ERROR] at query id {entry['id']}:")
            print(error)
            dbpedia_data = entry.get('dbpedia', {'predicted': {}, 'trg': {}})
            dbpedia_data[dbpedia_key]['query_result'] = error.args[0]
            dbpedia_data[dbpedia_key]['is_error'] = True
            entry['dbpedia'] = dbpedia_data

    return complete_report


def get_template_metrics(report: List[Dict]):
    templates_metrics: Dict = {}

    for entry in report:
        t_id = entry['template_id']

        template_info = templates_metrics.get(t_id, {'count': 0, 'exact_word_match': 0})
        template_info['count'] += 1
        if entry['correct']:
            template_info['exact_word_match'] += 1

        templates_metrics[t_id] = template_info

    # exact word match accuracy
    for t_id in templates_metrics:
        templates_metrics[t_id]['exact_word_match'] = f"{templates_metrics[t_id]['exact_word_match'] / templates_metrics[t_id]['count']:.0%}"

    # bleu score
    for t_id in templates_metrics:
        predicted = [entry['predicted'].split() for entry in report if entry['template_id'] == t_id]
        trg = [[entry['trg'].split()] for entry in report if entry['template_id'] == t_id]
        templates_metrics[t_id]['bleu_score'] = f"{bleu_score(predicted, trg):.0%}"

    # answer accuracy
    if 'dbpedia' in report[0]:
        for t_id in templates_metrics:
            answers = [(entry['dbpedia']['predicted'], entry['dbpedia']['trg']) for entry in report if entry['template_id'] == t_id]
            error_predicted_count = 0
            error_ground_truth_count = 0
            correct_answer_count = 0

            for a in answers:
                if a[0]['is_error']:
                    error_predicted_count += 1
                elif a[1]['is_error']:
                    error_ground_truth_count += 1
                elif a[0]['query_result'] == a[1]['query_result']:
                    correct_answer_count += 1

            n_template_entries = templates_metrics[t_id]['count']

            templates_metrics[t_id]['percent_error_predicted'] = f"{error_predicted_count/n_template_entries:.0%}"
            templates_metrics[t_id]['percent_error_ground_truth'] = f"{error_ground_truth_count/n_template_entries:.0%}"
            templates_metrics[t_id]['answer_accuracy'] = f"{correct_answer_count/n_template_entries:.0%}"
    else:
        print("No info available on answer accuracy")

    return templates_metrics


def get_full_report_metrics(report: List[Dict]):
    report_metrics = {}
    # exact word match
    exact_word_match_count = len([entry for entry in report if entry['correct']])
    report_metrics['exact_word_match'] = f"{exact_word_match_count / len(report):.0%}"

    # percentage empty requets

    # bleu score
    predicted = [entry['predicted'].replace(':', '_').split() for entry in report]
    trg = [[entry['trg'].replace(':', '_').split()] for entry in report]

    report_metrics['bleu_score'] = f"{bleu_score(predicted, trg)}"

    # answer accuracy
    if 'dbpedia' in report[0]:
        answers = [(entry['dbpedia']['predicted'], entry['dbpedia']['trg']) for entry in report]
        error_predicted_count = 0
        error_ground_truth_count = 0
        correct_answer_count = 0
        count_empty = 0

        for a in answers:
            if a[0]['is_error']:
                error_predicted_count += 1
            elif a[1]['is_error']:
                error_ground_truth_count += 1
            elif a[0] == a[1]:
                correct_answer_count += 1

            # if not a[1]['is_error'] and ('boolean' in a[1]['query_result'] and not a[1]['query_result']['boolean'] \
            #     or a[1]['query_result']['results']['bindings'] == []):
            #     count_empty += 1

        # report_metrics['percent_expected_empties'] = f"{count_empty/len(report)}"
        report_metrics['percent_error_predicted'] = f"{error_predicted_count/len(report)}"
        report_metrics['percent_error_ground_truth'] = f"{error_ground_truth_count/len(report)}"
        report_metrics['answer_accuracy'] = f"{correct_answer_count/len(report)}"
        
    else:
        print("No info available on answer accuracy")

    # entity accuracy
    symbols = list('abcdefghijklmnopqrstuvxyz0123456789')
    total_dist = 0
    total_len = 0
    for entry in report:
        tags = ['dbr', 'dbc', 'dbp', 'dbo']
        ground_truth = [w for w in entry['trg'].split() if w[:3] in tags]
        pred = [w for w in entry['predicted'].split() if w[:3] in tags]

        all = list(set(ground_truth + pred))

        if len(all) > len(symbols):
            raise ValueError('Not enough symbols to encode all entities, extend symbols!')

        encoding_dict = dict(zip(all, symbols))
        ref_str = ''.join([encoding_dict[w] for w in ground_truth])
        pred_str = ''.join([encoding_dict[w] for w in pred])

        # https://stackoverflow.com/a/68145930
        total_dist = total_dist + levenshtein_distance(ref_str, pred_str)
        total_len = total_len + len(ref_str) + len(pred_str)
        # not sure if this makes sense lol

    report_metrics['levenshtein'] = str((total_len - total_dist) / total_len)
    return report_metrics


def generate_report(error_report_path: str, run_template_metrics: bool, run_dbpedia: bool) -> List[Dict]:
    with open(error_report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)

    complete_report = generate_pure_sparql_for_report(report)
    print(len(complete_report))

    if run_dbpedia:
        print("QUERYING DBPEDIA FOR EXPECTED RESULT...")
        complete_report = query_dbpedia_for_report(complete_report, predicted=False)
        print("QUERYING DBPEDIA FOR PREDICTED RESULT...")
        complete_report = query_dbpedia_for_report(complete_report, predicted=True)

    full_report_metrics = get_full_report_metrics(complete_report)

    print('FULL REPORT:')
    for key, val in full_report_metrics.items():
        print(f'\t{key}: {val}')

    if run_template_metrics:
        template_metrics = get_template_metrics(complete_report)
        print('\nTEMPLATES REPORT:')
        for t_id in template_metrics:
            print(f'\tfor template {t_id}:')
            for key, val in template_metrics[t_id].items():
                print(f'\t\t{key}: {val}')

    return complete_report


def compare_reports(main_report: List[Dict], compared_report: List[Dict]):
    og_correct_ids = set([entry['id'] for entry in main_report if entry['correct']])
    copy_correct_ids = set([entry['id'] for entry in compared_report if entry['correct']])

    went_from_true_to_false = og_correct_ids.difference(copy_correct_ids)

    copy_correct_entries = [entry for entry in compared_report if entry['id'] in went_from_true_to_false]

    switched_templates: Dict = {} # template id of the entries that were correctly predicted without copy but incorrect with copy

    for entry in copy_correct_entries:
        ids_list = switched_templates.get(entry['template_id'], [])
        ids_list.append(entry['id'])
        switched_templates[entry['template_id']] = ids_list

    if len(switched_templates.keys()) > 0:
        print('COMPARED REPORT:')
        for key, val in switched_templates.items():
            print(f'\t{key}: {val}')

def main(error_report_path: str, error_report_path_to_compare: str, run_template_metrics: bool = False, run_dbpedia: bool = False) -> None:
    main_report = generate_report(error_report_path, run_template_metrics, run_dbpedia)

    if error_report_path_to_compare is not None:
        compare_report = generate_report(error_report_path_to_compare, run_template_metrics, run_dbpedia)

        compare_reports(main_report, compare_report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate accuracy of test set")

    parser.add_argument("--in", dest='in_file', type=str, default="reports/lcquad_split-lcquad_data-model_transformer/error_report.json",
                        help="path to the json file containing the generated error report")

    parser.add_argument("--in2", dest='in_file_2', type=str, default=None,
                        help="path to the json file containing the generated error report, optional to compare metrics before and after copy")

    parser.add_argument("--dbpedia", action='store_true', default=False,
                    help="set to true if you want to query dbpedia (answer accuracy metric")

    parser.add_argument("--template", action='store_true', default=False,
                    help="set to true if you want the accuracy per template")


    args = parser.parse_args()
    main(args.in_file, args.in_file_2, args.template, args.dbpedia)