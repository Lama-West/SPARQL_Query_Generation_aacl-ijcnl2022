import argparse
import json
from typing import Dict, List
from classes.lcquad_dataset import LCQUADDataset

def load_templates(path: str) -> List[Dict]:
    with open(path, 'r', encoding='utf-8') as f:
        templates: List[Dict] = json.load(f)
    return templates

def main(args: argparse.Namespace) -> None:
    processed_dataset = LCQUADDataset(args.train, args.test) #, (args.dbr, args.dbp, args.dbc, args.dbo))
    templates = load_templates(args.templates)
    processed_dataset.tag_templated_questions(templates)
    processed_dataset.untag_elems_not_predictable(untag_all=False)

    if args.tntspa:
        tntspa_dataset = LCQUADDataset()
        tntspa_dataset.load_tntspa((args.train_nl, args.train_sparql), (args.test_nl, args.test_sparql))
        processed_dataset.get_tntspa_split_dataset(tntspa_dataset)

    processed_dataset.save(f'{args.out_dir}/dataset.json')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build expected format dataset from lcquad.")

    parser.add_argument("--train", type=str, default='raw_data/LC-QuAD/official/train-data.json',
                        help="path to the json file containing the train original lcquad dataset")

    parser.add_argument("--test", type=str, default='raw_data/LC-QuAD/official/test-data.json',
                        help="path to the json file containing the test original lcquad dataset")

    parser.add_argument("--templates", type=str, default='out_data/LC-QuAD/corrected_templates.json',
                        help="path to the json file containing the (modified) lcquad templates")

    parser.add_argument("--tntspa", action="store_true", default=False,
                        help="Generate resplit dataset from tntspa data")

    parser.add_argument("--train_nl", type=str, default='raw_data/LC-QuAD/tntspa/train.en',
                        help="path to the json file containing the english train txt file")

    parser.add_argument("--train_sparql", type=str, default='raw_data/LC-QuAD/tntspa/train.sparql',
                        help="path to the json file containing the sparql train txt file")

    parser.add_argument("--test_nl", type=str, default='raw_data/LC-QuAD/tntspa/test.en',
                        help="path to the json file containing the english test txt file")

    parser.add_argument("--test_sparql", type=str, default='raw_data/LC-QuAD/tntspa/test.sparql',
                        help="path to the json file containing the sparql test txt file")

    parser.add_argument("--out_dir", type=str, default='out_data/LC-QuAD',
                        help="path to save all data")


    args = parser.parse_args()

    if not args.train or not args.test:
        parser.error(
            "This program requires values for --train and --test")

    if (args.tntspa) and (args.train_nl is None or args.train_sparql is None or args.test_nl is None or args.test_sparql is None):
        parser.error(
            "--resplit requires --train_nl, --train_sparql, --test_nl and --test_sparql.")

    main(args)
