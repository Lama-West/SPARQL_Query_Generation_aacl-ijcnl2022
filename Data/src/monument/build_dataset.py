import argparse
import json
from classes.monument_dataset import MonumentDataset

def main(args: argparse.Namespace) -> None:
    processed_dataset = MonumentDataset(args.nl, args.sparql, args.templates)
    processed_dataset.save(f'{args.out_dir}/dataset.json')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build expected format dataset from monument.")

    parser.add_argument("--nl", type=str, default='raw_data/Monument/base/data.en',
                        help="path to the txt file containing the natural language monument data")

    parser.add_argument("--sparql", type=str, default='raw_data/Monument/base/data.sparql',
                        help="path to the txt file containing the interm sparql monument data")

    parser.add_argument("--templates", type=str, default='out_data/Monument/templates.json',
                help="path to the json file containing the templates")

    parser.add_argument("--out_dir", type=str, default='out_data/Monument/base',
                        help="path to save all data")


    args = parser.parse_args()

    if not args.nl or not args.sparql:
        parser.error(
            "This program requires values for --nl and --sparql")

    main(args)
