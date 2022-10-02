import re

REPLACEMENTS = [
    ['dbo:', 'http://dbpedia.org/ontology/', 'dbo_'],
    ['dbp:', 'http://dbpedia.org/property/', 'dbp_'],
    ['dbc:', 'http://dbpedia.org/resource/Category:', 'dbc_'],
    ['dbr:', 'res:', 'http://dbpedia.org/resource/', 'dbr_'],
    ['dct:', 'dct_'],
    ['geo:', 'geo_'],
    ['georss:', 'georss_'],
    ['rdf:', 'rdf_'],
    ['rdfs:', 'rdfs_'],
    ['foaf:', 'foaf_'],
    ['owl:', 'owl_'],
    ['yago:', 'yago_'],
    ['skos:', 'skos_'],
    [' ( ', '  par_open  '],
    [' ) ', '  par_close  '],
    [' ( ', ' sparql_open '],
    [' ) ', ' sparql_close '],
    ['(', ' attr_open '],
    [') ', ')', ' attr_close '],
    ['{', ' brack_open '],
    ['}', ' brack_close '],
    [' . ', ' sep_dot '],
    ['. ', ' sep_dot '],
    ['?', 'var_'],
    ['*', 'wildcard'],
    [' <= ', ' math_leq '],
    [' >= ', ' math_geq '],
    [' < ', ' math_lt '],
    [' > ', ' math_gt ']
]


URI_SHORTENERS = [
    {
        'match': 'http://dbpedia.org/ontology/',
        'interm_sparql': 'dbo_',
        'pure_sparql': 'dbo:'
    },
    {
        'match': 'http://dbpedia.org/property/',
        'interm_sparql': 'dbp_',
        'pure_sparql': 'dbp:'
    },
    {
        'match': 'http://dbpedia.org/resource/Category:',
        'interm_sparql': 'dbc_',
        'pure_sparql': 'dbc:'
    },
    {
        'match': 'http://dbpedia.org/resource/',
        'interm_sparql': 'dbr_',
        'pure_sparql': 'dbr:'
    },
    {
        'match': 'dbo:',
        'interm_sparql': 'dbo_',
        'pure_sparql': 'dbo:'
    },
    {
        'match': 'dbp:',
        'interm_sparql': 'dbp_',
        'pure_sparql': 'dbp:'
    },
    {
        'match': 'dbc:',
        'interm_sparql': 'dbc_',
        'pure_sparql': 'dbc:'
    },
    {
        'match': 'dbr:',
        'interm_sparql': 'dbr_',
        'pure_sparql': 'dbr:'
    },
]


PURE_SPARQL_TO_INTERM = [
    {
        'pure_sparql': 'dct:',
        'interm_sparql': 'dct_'
    },
    {
        'pure_sparql': 'geo:',
        'interm_sparql': 'geo_'
    },
    {
        'pure_sparql': 'georss:',
        'interm_sparql': 'georss_'
    },
    {
        'pure_sparql': 'rdf:',
        'interm_sparql': 'rdf_'
    },
    {
        'pure_sparql': 'rdfs:',
        'interm_sparql': 'rdfs_'
    },
    {
        'pure_sparql': 'foaf:',
        'interm_sparql': 'foaf_'
    },
    {
        'pure_sparql': 'owl:',
        'interm_sparql': 'owl_'
    },
    {
        'pure_sparql': 'yago:',
        'interm_sparql': 'yago_'
    },
    {
        'pure_sparql': 'skos:',
        'interm_sparql': 'skos_'
    },
    {
        'pure_sparql': '(',
        'interm_sparql': '  par_open  '
    },
    {
        'pure_sparql': ')',
        'interm_sparql': '  par_close  '
    },
    {
        'pure_sparql': '{',
        'interm_sparql': '  brack_open  '
    },
    {
        'pure_sparql': '}',
        'interm_sparql': '  brack_close  '
    },
    {
        'pure_sparql': '.',
        'interm_sparql': '  sep_dot  '
    },
    {
        'pure_sparql': '?',
        'interm_sparql': ' var_'
    },
    {
        'pure_sparql': '*',
        'interm_sparql': '  wildcard  '
    },
    {
        'pure_sparql': ' <= ',
        'interm_sparql': ' math_leq '
    },
    {
        'pure_sparql': ' >= ',
        'interm_sparql': ' math_geq '
    },
    {
        'pure_sparql': ' < ',
        'interm_sparql': ' math_lt '
    },
    {
        'pure_sparql': ' > ',
        'interm_sparql': ' math_gt '
    }
]


PURE_SPARQL_TO_INTERM_RES = [
    {
        'pure_sparql': '(',
        'interm_sparql': ' attr_open '
    },
    {
        'pure_sparql': ')',
        'interm_sparql': ' attr_close '
    }
]


PLACEHOLDERS = {
    'dbo': '<ontology>',
    'dbp': '<property>',
    'dbc': '<category>',
    'dbr': '<resource>'
}

# when replacing var_uri by ?uri, sometimes catches resources containing var (ex: Sarovar_Bridge becomes Saro?Bridge). This regex is used to revert this change in resources but not in variables
CATCH_VAR_IN_RESOURCE_NAME_RE = re.compile('db[rocp]:[a-zA-Z0-9_]*?(\?)[a-zA-Z0-9]', flags = re.IGNORECASE)

# in interm sparql, ORDER BY DESC(?uri)  become _obd_ var_uri
REPLACE_ORDER_BY_RE = re.compile(".*((_ob[ad]_)\\s*(\\?[a-zA-Z]+))", flags = re.IGNORECASE)

# Catch resources in pure sparql queries
GET_RESOURCES_PURE_SPARQL_RE = re.compile("(db[orcp]:.*?)(?:[\s|}])", flags=re.IGNORECASE)

# splits a uri into the resource type part (entity, ontology, property, etc) and the resource name part
SPLIT_URI_RE = re.compile('https?:\/\/dbpedia.org\/(.*?)\/(.*)', re.IGNORECASE)

# This will capture everything that is between <>, especially useful for LCQUAD
FIND_RESOURCES_BTW_ANGLE_BRACKETS_RE = re.compile('\<(.*?)\>', re.IGNORECASE)

# This will capture everything except what is in resources
RE_TEMPLATE_EXCLUDE_SPECIFIC_RESOURCES = '(.*?)({resources}|$)'

# this is used to capture parentheses (attr_open and par_close) that follow a filter in interm sparql
REPLACE_FILTER_PAR_RE = re.compile("(?:FILTER)\s*?(par_open).*(par_close)", re.IGNORECASE)

# this is used to capture parentheses (attr_open and par_close) that follow a count or an order by in interm sparql
REPLACE_REST_PAR_RE = re.compile("(?:count|order by (?:asc|desc))\s*?(par_open).*?(par_close)", re.IGNORECASE)

# this is used to capture quotes that follow a regex in interm sparql to encode them into the 'quote' symbol
REPLACE_QUOTES_RE = re.compile("regex par_open var_[a-z]+,(').*?(')(?:,(').*?('))? par_close", re.IGNORECASE)

# most math clauses in raw interm sparql have no spaces, so this regex is used to insert some
INSERT_SPACES_MATH_RE = re.compile("(var_[a-zA-Z0-9]+)(math_[gl]t)(.*?)[$|\s]", re.IGNORECASE)

# Master regex to catch resources in interm sparql queries in ANY dataset
GET_RESOURCES_INTERM_SPARQL_RE = re.compile("(db[orcp]_.*?(?:(?:\s*?(?:attr|par)_open([a-z^db[orcp]_*?)(?:attr|par)_close [a-z^db[orcp]]*?)|(?:\s*?(?:attr|par)_open(.*?)(?:attr|par)_close)|(?:\s?_.*?)|(?:,?_.*?)|(?:\s*?\-.*?))*\??)(?:\s|brack_close)")

# https://stackoverflow.com/a/29922050 - split a resource name that is encoded in camel case into different words
CAMEL_CASE_SPLIT_RE = re.compile(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)')

# Abbreviations for different types in sparql
RESOURCE_ABBRV = 'dbr'
PROPERTY_ABBRV  = 'dbp'
CLASS_ABBRV = 'dbo'

# Names for different types in sparql
RESOURCE_TYPE = 'resource'
PROPERTY_TYPE = 'property'
CLASS_TYPE = 'ontology'


# Exceptions to handle when correcting sep dots (useful for DBNQA because lots of formatting errors with sep dots)
EXCEPTIONS_NOT_REPLACE = [ 'dbr_Mode._Set._Clear.', 'dbr_Cand.theol.', 'dbr_Observe._Hack._Make.']
ENDS_EXCEPTIONS_NOT_REPLACE = ['dept.', 'bros.', 'litt.', 'corp.', 'gent.']
ENDS_EXCEPTIONS_REPLACE = ['hop.']

# Sparql explicit type for rdf:type, should not be counted as a resource
SPARQL_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"