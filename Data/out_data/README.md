# OUT DATA

We focus on the two main datasets used in the most relevant articles: Monument and LC-QuAD (v1.0). We produce a standard dataset entry that has the form:

- `_id: Union[int, str]` - the entry id
- `template_id: Union[int, str]` - the template id if there is one
- `question: str` - the natural language question
- `uri_question: str` - the natural language question where resources are replaced by their uri
- `interm_sparql: str` - the intermediary sparql question (a sparql query using words instead of symbols)
- `uri_interm_sparql: str` - the intermediary sparql question where resources are replaced by their uri
- `pure_sparql: str` - the (supposed to be) working sparql query
- `set: str` - 'train', 'valid' or 'test'
- `original_data: Dict` - a dictionary containing the raw data from which the entry was generated
- `dpedia_result: Dict` - the dbpedia query result (optional)

here is an example of a generated entry:

```json
{
    "_id": "214",
    "template_id": 1,
    "question": "is anti-air war memorial a place",
    "uri_question": "is dbr:Anti-Air_War_Memorial a dbo:Place",
    "interm_sparql": "ask where brack_open dbr_Anti-Air_War_Memorial rdf_type dbo_Place brack_close",
    "uri_interm_sparql": "ask where brack_open dbr:Anti-Air_War_Memorial rdf_type dbo:Place brack_close",
    "pure_sparql": "ask where { dbr:Anti-Air_War_Memorial rdf:type dbo:Place }",
    "set": "ask where { dbr:Anti-Air_War_Memorial rdf:type dbo:Place }",
    "original_data": {
        "question": "is anti-air war memorial a place",
        "interm_sparql": "ask where brack_open dbr_Anti-Air_War_Memorial rdf_type dbo_Place brack_close"
    }
}
```

Here are the data entries for all different runs:
All Monuments, original data:
```
    - Question: entry['original_data']['question']
    - Query: entry['original_data']['interm_sparql']
```
All Monuments, corrected data:
```
    - Question: entry['question']
    - Query: entry['interm_sparql']
```
All Monuments, tagged data:
```
    - Question: entry['uri_question']
    - Query: entry['uri_interm_sparql']
```

LC-QuAD Corrected Questions, original data:
```
    - Question: entry['original_data']['lcquad.corrected_question']
    - Query: entry['interm_sparql'] (The interm SPARQL is generated directly from entry['original_data']['lcquad.sparql_query'])
    - Set: entry['set'] (There was no official test-val split, so we split it randomly 50-50)
```

LC-QuAD Interm Questions, original data:
```
    - Question: entry['original_data']['tagged.baseline_question'] (the uniformized version of lcquad.intermediary_question)
    - Query: entry['interm_sparql']
    - Set: entry['set']
```

TNTSPA, original data:
```
    - Question: entry['original_data']['tntspa.question']
    - Query: entry['original_data']['tntspa.interm_sparql']
    - Set: entry['original_data']['tntspa.set']
```

LC-QuAD Corrected Questions, corrected data:
```
    - Question: entry['question']
    - Query: entry['interm_sparql']
    - Set: entry['set']
```

LC-QuAD Interm Questions, tagged data:
```
    - Question: entry['original_data']['tagged.question']
    - Query: entry['interm_sparql']
    - Set: entry['set']
```