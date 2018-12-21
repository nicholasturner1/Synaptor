__doc__ = """
Database functionality through SQLAlchemy
"""

import re
import sqlalchemy as sa
import pandas as pd


__all__ = ["open_db_metadata", "create_db_tables",
           "execute_db_statement", "execute_db_statements",
           "read_dframe", "write_dframe"]


# Pool of engines to databases used so far
ENGINES = dict()
# Pulling these from
# https://docs.sqlalchemy.org/en/latest/core/engines.html#supported-databases
REGEXPS = [re.compile("postgresql\+psycopg2://"),
           re.compile("postgresql://"),
           re.compile("postgresql\+pg8000://"),
           re.compile("mysql://"),
           re.compile("mysql\+mysqldb://"),
           re.compile("mysql\+mysqlconnector://"),
           re.compile("mysql\+oursql://"),
           re.compile("oracle://"),
           re.compile("oracle\+cx_oracle://"),
           re.compile("mssql\+pyodbc://"),
           re.compile("mssql\+pymssql://"),
           re.compile("sqlite:///")]


def init_engine(url):
    if url not in ENGINES:
        ENGINES[url] = sa.create_engine(url)

    return ENGINES[url]


def open_db_metadata(url):
    engine = init_engine(url)

    metadata = sa.MetaData()
    metadata.reflect(bind=engine)

    return metadata


def create_db_tables(url, metadata):
    engine = init_engine(url)
    metadata.create_all(engine)


def drop_db_tables(url, metadata, tables=None):
    engine = init_engine(url)
    metadata.drop_all(engine, tables=tables)
    return open_db_metadata(url)


def execute_db_statement(url, statement):
    engine = init_engine(url)
    return engine.execute(statement)


def execute_db_statements(url, statements):
    engine = init_engine(url)

    results = list()
    with engine.begin() as connection:
        for statement in statements:
            res = connection.execute(statement)
            results.append(res)

    return results


def read_dframe(url, statement, index_col=None):
    engine = init_engine(url)
    return pd.read_sql_query(statement, engine, index_col=index_col)


def read_dframes(url, statements, index_cols=None):
    """ Read multiple tables as a single transaction. """
    if index_cols is None:
        index_cols = list(None for _ in statements)

    assert len(statements) == len(index_cols)
    engine = init_engine(url)

    results = list()
    with engine.begin() as connection:
        for (statement, index_col) in zip(statements, index_cols):
            new_dframe = pd.read_sql_query(statement, connection,
                                           index_col=index_col)
            results.append(new_dframe)

    return results


def write_dframe(dframe, url, table, if_exists="append", index=True):
    engine = init_engine(url)
    dframe.to_sql(table, engine, if_exists=if_exists, index=index)


def write_dframes(dframes, url, tables, if_exists="append", index=True):
    """ Write multiple tables as a single transaction. """
    assert len(dframes) == len(tables)
    engine = init_engine(url)

    with engine.begin() as connection:
        for (dframe, table) in zip(dframes, tables):
            dframe.to_sql(table, connection, if_exists=if_exists, index=index)
