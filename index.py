import re
from csv import DictReader
from unidecode import unidecode

import duckdb
from pyphonetics import Metaphone

WINES_FILE_PATH = "wines.csv"
WINES_DUCKDB_PATH = "wines.duckdb"
IGNORE_REGEXP = "(\\.|[^a-z0-9])+"


def strip_accents(s):
    return unidecode(s)


def normalize(s):
    """This is the default way that DuckDB's full-text search extension
    normalizes strings with one exception: we retain digits, which are
    important for wine vintage."""
    return re.sub(IGNORE_REGEXP, " ", strip_accents(s).lower())


def tokenize(s):
    return normalize(s).split()


def get_metaphone(s):
    """Returns the Metaphone for a given string.

    The Metaphone package ignores non-alphabet characters, including whitespace:

    >>> from pyphonetics import Metaphone
    >>> m = Metaphone()
    >>> m.phonetics("champ onion")
    'XMPNN'
    >>> m.phonetics("champ")
    'XMP'
    >>> m.phonetics("onion")
    'ONN'"""
    return Metaphone().phonetics(s)


def get_metaphone_tokens(s):
    """Tokenizes a string and returns all the tokens' Metaphones.

    >>> get_metaphone_tokens("chateau champignon")
    ['XT', 'XMPNN']"""

    return [get_metaphone(t) for t in tokenize(s)]


def get_all_wine_records():
    """Returns a list of dictionary records with names of wines:

    [
        {'name': 'Bucci Villa Bucci Riserva Verdicchio 2013 750ml'},
        {'name': 'Villa Venti "Primo Segno" Sangiovese di Romagna 2019 750ml'},
        ...
    ]
    """

    with open(WINES_FILE_PATH) as wines_file:
        reader = DictReader(open(WINES_FILE_PATH))
        return [record for record in reader]


def prepare_indexes(wine_records, token_metaphone_map):
    conn = duckdb.connect(WINES_DUCKDB_PATH)

    # Create a table containing all our wines
    col_defs = ", ".join(
        [
            "id integer primary key",
            "name text not null",
            "exact_metaphone text not null",
            "metaphone_tokens text not null",
        ]
    )
    conn.execute(f"CREATE TABLE wines ({col_defs})")
    conn.executemany(
        "INSERT INTO wines VALUES (?, ?, ?, ?)",
        [
            (r["id"], r["name"], r["exact_metaphone"], r["metaphone_tokens"])
            for r in wine_records
        ],
    )

    # Create a full-text search index on the wine names and metaphone tokens.
    #
    # - The wine name index is used for accurate transcriptions.
    # - The metaphone token index is for our Metaphone Token queries.
    #
    # We can choose which field to search ('name' or 'metaphone_tokens')
    # at query time using DuckDB's FTS extension.
    conn.execute(
        f"PRAGMA create_fts_index('wines', 'id', 'name', 'metaphone_tokens', ignore='{IGNORE_REGEXP}')"
    )

    # Create a table containing our token-to-metaphone mapping.
    #
    # This table is a utility for our Similar Token Metaphone queries.
    col_defs = ", ".join(["token text not null", "metaphone text not null"])
    conn.execute(f"CREATE TABLE token_metaphones ({col_defs})")
    conn.executemany(
        f"INSERT INTO token_metaphones VALUES (?, ?)", token_metaphone_map.items()
    )


def main():
    wine_records = get_all_wine_records()

    # First, enrich each record with data we need for our indexes:
    #
    # [
    #    ...
    #    {'id': 1541,
    #     'name': 'Bodega Chacra Sin Azufre Pinot Noir 2017 750ml',
    #     'exact_metaphone': 'BTKXKRSNSFRPNTNRML',
    #     'metaphone_tokens': 'BTK XKR SN ASFR PNT NR ML'}
    #    ...
    # ]

    for i, record in enumerate(wine_records):
        record["id"] = i + 1  # 1-index the record IDs
        record["exact_metaphone"] = get_metaphone(record["name"])
        record["metaphone_tokens"] = " ".join(get_metaphone_tokens(record["name"]))
        record["tokens"] = tokenize(record["name"])

    # Now, create a mapping of each token in our index to its Metaphone -- this
    # is for our Similar Token Metaphone query approach:
    #
    # {
    #   ...
    #   'urbajs': 'URBJS',
    #   'urbano': 'URBN',
    #   'uva': 'UF',
    #   'vaillons': 'FLNS',
    #   'vajra': 'FJR',
    #   'val': 'FL',
    #   'valbuena': 'FLBN',
    #   'valentino': 'FLNTN',
    #   ...
    # }

    token_metaphone_map = {}
    for record in wine_records:
        tokens = tokenize(record["name"])
        for t in tokens:
            if t in token_metaphone_map:
                continue
            token_metaphone_map[t] = get_metaphone(t)

    prepare_indexes(wine_records, token_metaphone_map)


if __name__ == "__main__":
    main()
