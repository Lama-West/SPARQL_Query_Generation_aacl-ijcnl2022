# Knowledge Base-aware SPARQL Query Translation from Natural Language

Welcome to our repo!

Automatic SPARQL query generation from natural language questions has seen recent progress with the development of neural machine translation models. However, these models do not consider the schema of the knowledge base and generally adopt a standard sequence to sequence approach. Consequently, while they appear to learn the SPARQL syntax quite efficiently, they display some limitations when it comes to generating the appropriate resources, classes and properties in the SPARQL queries. To deal with these issues, we present an approach that enhances state-of-the-art neural architectures with a copy mechanism. This copy layer learns to identify and copy knowledge base elements (schema, resources) from natural language questions. We evaluate our approach on standard datasets based on the machine translation metric BLEU. We also execute the SPARQL queries and evaluate the answers' accuracy. Our results show that our approach increases the BLEU score significantly as well as the accuracy of the answers, and the models’ ability to handle unknown knowledge base elements.

## Contents

This is the repo that contains all the code necessary to train and test [ConvS2S](notebooks/ConvS2S.ipynb) and [Transformer S2S](notebooks/Transformer.ipynb) with and without the copy layer. This code is built for Colab and will need minor adaptations to run on your local machine.
All the data is in the [Data repository](https://anonymous.4open.science/r/KB_Aware_SPARQL_NMT-DATA/README.md).

## Pretrained Models

All the models evaluated in our article are available on [Google Drive](https://drive.google.com/drive/folders/1rCgKqXotehh4Bprgu8R7BEsWU3HKXWkw?usp=sharing)

## Next steps

The next steps for this repo is to adapt the code on colab in a python module that is easily installable and runnable anywhere.
