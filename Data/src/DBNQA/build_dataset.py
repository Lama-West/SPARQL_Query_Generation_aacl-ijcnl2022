import argparse
from classes.dbnqa_dataset import DBNQADataset

def main(args: argparse.Namespace) -> None:
    processed_dataset = DBNQADataset(args.nl, args.sparql, subset=args.subset)
    processed_dataset.save(f'{args.out_dir}/dataset.json')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build expected format dataset from lcquad.")

    parser.add_argument("--nl", type=str, default='raw_data/DBNQA/data.en',
                        help="path to the json file containing the train original lcquad dataset")

    parser.add_argument("--sparql", type=str, default='raw_data/DBNQA/data.sparql',
                        help="path to the json file containing the test original lcquad dataset")

    parser.add_argument("--out_dir", type=str, default='out_data/DBNQA',
                        help="path to save all data")
    
    parser.add_argument("--subset", type=int, default=None,
                        help="create a subset of size N")


    args = parser.parse_args()

    if not args.nl or not args.sparql:
        parser.error(
            "This program requires values for --train and --test")

    main(args)
