import sys
import pprint

import duckdb
from jarowinkler import jarowinkler_similarity

from index import (
    WINES_DUCKDB_PATH,
    get_metaphone,
    get_metaphone_tokens,
    tokenize,
    normalize,
)

RESULTS_PER_QUERY_APPROACH = 10


def get_connection():
    return duckdb.connect(WINES_DUCKDB_PATH)


def get_wines():
    conn = get_connection()
    return conn.sql("select * exclude (id) from wines").df()


def get_top_k_matches(transcript, k=5):
    if transcript == "":
        return []

    conn = get_connection()

    # Lowercase the transcript, strip accents, ignore non-alphanumeric characters.
    transcript = normalize(transcript)

    matches = set()

    # Collect deduplicated results from all 5 query approaches.
    matches.update(
        duckdb_full_text_query(conn, transcript),
        exact_metaphone_query(conn, transcript),
        metaphone_token_query(conn, transcript),
        similar_token_metaphones_query(conn, transcript),
        metaphone_substring_query(conn, transcript),
    )

    # Compute Jaro-Winkler similarity scores between all matches and the original
    # transcript.
    matches = [
        {"match": match, "similarity_score": jarowinkler_similarity(match, transcript)}
        for match in matches
    ]

    # Rank results: `jarowinkler_similarity` scores similar strings higher.
    matches = sorted(matches, key=lambda m: m["similarity_score"], reverse=True)

    # Dispose of the scores before returning.
    return [m["match"] for m in matches][:k]


def duckdb_full_text_query(conn, transcript, n=RESULTS_PER_QUERY_APPROACH):
    sql = _duckdb_fts_sql("wines", transcript, "name", n)
    return [tup[0] for tup in conn.sql(sql).fetchall()]


def exact_metaphone_query(conn, transcript, n=RESULTS_PER_QUERY_APPROACH):
    query = get_metaphone(transcript)
    sql = f"""
    select name
    from wines
    where exact_metaphone = '{query}'
    limit {n}
    """
    return [tup[0] for tup in conn.sql(sql).fetchall()]


def metaphone_token_query(conn, transcript, n=RESULTS_PER_QUERY_APPROACH):
    query = " ".join(get_metaphone_tokens(transcript))
    sql = _duckdb_fts_sql("wines", query, "metaphone_tokens", n)
    return [tup[0] for tup in conn.sql(sql).fetchall()]


def similar_token_metaphones_query(conn, transcript, n=RESULTS_PER_QUERY_APPROACH):
    tokens = tokenize(transcript)
    similar_tokens = {}

    # Get all tokens in our index that are 1 edit distance away.
    for token in tokens:
        sql = f"""
        select token, metaphone
        from token_metaphones
        where levenshtein('{token}', token) == 1
        """
        results = conn.sql(sql).fetchall()
        for tup in results:
            similar_tok = tup[0]
            similar_tokens[similar_tok] = None

    # Now do a Metaphone Token Query using all those similar tokens.
    query = " ".join(similar_tokens.keys())
    return metaphone_token_query(conn, query, n)


def metaphone_substring_query(conn, transcript, n=RESULTS_PER_QUERY_APPROACH):
    query = get_metaphone(transcript)

    sql = f"""
    select name
    from wines
    where regexp_matches(exact_metaphone, '{query}')
    limit {n}
    """

    return [tup[0] for tup in conn.sql(sql).fetchall()]


def _duckdb_fts_sql(table_name, search_query, field, limit):
    return f"""
    select name, score
    from
      (select name, fts_main_{table_name}.match_bm25(id, '{search_query}', fields := '{field}') as score from wines)
    where score is not null
    order by score desc
    limit {limit}
    """


def main():
    pprint.pprint(get_top_k_matches(sys.argv[1]))


if __name__ == "__main__":
    main()
