# SRC

This folder contains all the code used to generate the datasets. It is organized as follow:

## Classes

This folder contains the base classes used to help with organization. The Dataset class is abstract and is the parent
class of all specific datasets implementations: DBNQADataset, LCQUADDataset and MonumentDataset.

The Entry class represents a standard entry in the produced datasets.

## Common

This folder contains helper scripts and utils used for generation and evaluation of the datasets.

- [answer_accuracy.py](answer_accuracy.py) takes as input an error report generated by training and inference of a model and evaluates the accuracy score of the sparql queries
- [dataset_statistics.py](dataset_statistics.py) a quick script that calculates interesting dataset metrics including the intersection rate
- [build_uri_vocab.py](build_uri_vocab.py) is a helper to build an expressions dictionnary representing all the ways one can refer to a dbpedia entity
- [consts.py](consts.py) contains all constants and regexes used in this project
- [interm_sparql_to_pure_sparql.py](interm_sparql_to_pure_sparql.py) contains helper functions to go from an intermediary sparql query to a runnable one
- [query_dbpedia.py](query_dbpedia.py) contains helper functions to run queries on dbpedia. It can also be used as a standalone script
- [re_callbacks.py](re_callbacks.py) contains all callbacks used by re.sub throughout the code
- [utils.py](utils.py) contains generic util functions

## DBNQA

This folder contains scripts specific to the DBNQA dataset architecture.

## LCQUAD

This folder contains scripts specific to the LCQuAD v1.0 dataset architecture.

Some entries are super broken and have to be fixed by hand!
ids: 577, 1583, 2321, 4076, 3631, 620, 1777, 2331, 4103, 1544, 2681, 3993

## Monument

This folder contains scripts specific to the Monument dataset architecture.