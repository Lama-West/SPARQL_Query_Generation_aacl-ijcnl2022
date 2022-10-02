# Knowledge Base-aware SPARQL Query Translation from Natural Language

Welcome to our repo!

Automatic SPARQL query generation from natural language questions has seen recent progress with the development of neural machine translation models. However, these models do not consider the schema of the knowledge base and generally adopt a standard sequence to sequence approach. Consequently, while they appear to learn the SPARQL syntax quite efficiently, they display some limitations when it comes to generating the appropriate resources, classes and properties in the SPARQL queries. To deal with these issues, we present an approach that enhances state-of-the-art neural architectures with a copy mechanism. This copy layer learns to identify and copy knowledge base elements (schema, resources) from natural language questions. We evaluate our approach on standard datasets based on the machine translation metric BLEU. We also execute the SPARQL queries and evaluate the answers' accuracy. Our results show that our approach increases the BLEU score significantly as well as the accuracy of the answers, and the models’ ability to handle unknown knowledge base elements.

The pretrained models and code are in the [Model repository](https://anonymous.4open.science/r/KB_Aware_SPARQL_NMT-MODELS/README.md)

## Installation

To install and run this repository on your computer, you need Python 3.7+

Install the requirements with the command `py -m pip install -r requirements.txt`

Then, build the repo with the command `py -m build .`

Finally, install the repo with the command `py -m pip install .`

## Quick Run

This repository focuses on generating the data for the associated Models repository. As such, you might not need to regenerate anything since all the datasets are available in the out_data/ folder.
However, if you want to try it out, you can generate a clean version of the monument 50 dataset like so:

`py src/monument --nl raw_data/Monument/50/data.en --sparql raw_data/Monument/base/data.sparql --out_dir out_data/Monument/50`

One of the goal of this repository is that it is flexible enough to allow anyone to upload their SPARQL data and generate a standard version dataset.
Other interesting scripts include `src/common/answer_accuracy.py` which takes as input one (or two) error reports to get the answer accuracy results
presented in the paper.

## Organization

- [raw_data](raw_data/README.md): Folder containing source datasets referenced in our paper
- [out_data](out_data/README.md): Folder containing standardized and cleaned up datasets
- [src](src/README.md): Folder containing all necessary scripts to sanitize data

## Datasets

We focus on the two main datasets used in the most relevant articles: Monument and LC-QuAD (v1.0). We produce a standard dataset entry that has the form:

| Name        | Type            | Description                     |
|-------------|-----------------|---------------------------------|
| _id         | Union[int, str] | The entry id                    |
| template_id | Union[int, str] | The template id if there is one |
| question    | str             | The natural language question|
| uri_question    | str             |  The natural language question where resources are replaced by their uri|
| interm_sparql    | str             | The intermediary sparql query|
| uri_interm_sparql    | str             | The intermediary sparql question where resources are replaced by their uri|
| pure_sparql    | str             | The working interm sparql query|
| set    | Dict             | 'train', 'valid' or 'test'|
| original_data    | Dict             | A dictionary containing the raw data from which the entry was generated|

Here is an example of a generated entry:

```json
{
        "_id": "214",
        "template_id": 1,
        "question": {
            "question": "is anti-air war memorial a place ?",
            "uri_question_only_resources": "is dbr:Anti-Air_War_Memorial a dbo:Place ?",
            "uri_question_rest_no_resources": "is anti-air war memorial a place ?",
            "uri_question_all": "is dbr:Anti-Air_War_Memorial a dbo:Place ?"
        },
        "query": {
            "interm_sparql": "ask where brack_open dbr_Anti-Air_War_Memorial rdf_type dbo_Place brack_close",
            "uri_interm_sparql_only_resources": "ask where brack_open dbr:Anti-Air_War_Memorial rdf_type dbo:Place brack_close",
            "uri_interm_sparql_rest_no_resources": "ask where brack_open dbr_Anti-Air_War_Memorial rdf_type dbo_Place brack_close",
            "uri_interm_sparql_all": "ask where brack_open dbr:Anti-Air_War_Memorial rdf_type dbo:Place brack_close",
            "pure_sparql": "ask where { dbr:Anti-Air_War_Memorial rdf:type dbo:Place }"
        },
        "set": "train",
        "original_data": {
            "question": "is anti-air war memorial a place",
            "interm_sparql": "ask where brack_open dbr_Anti-Air_War_Memorial rdf_type dbo_Place brack_close"
        }
    },
```

Monument is a dataset containing 14788 entries, generated from 38 templates. <br>
LC-QuAD is a dataset containing 5000 entries, generated from 44 templates. <br>
DBNQA is too big to be included in this repo, but can be found [here](https://figshare.com/articles/dataset/Question-NSpM_SPARQL_dataset_EN_/6118505).
