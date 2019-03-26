""" Database functionality through SQLAlchemy """

import re
import shutil
import tempfile
import sqlalchemy as sa
import psycopg2
import pandas as pd

from . import local


__all__ = ["open_db_metadata", "create_db_tables",
           "execute_db_statement", "execute_db_statements",
           "read_dframe", "write_dframe_direct", "write_dframe_copy_from"]

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


def execute_db_statement(url, statement, num_retries=3):
    engine = init_engine(url)

    for i in range(num_retries):
        try:
            engine.execute(statement)
            break
        except sa.exc.DatabaseError as e:
            # connection likely stale, retrying...
            print(e)
            print("Retrying...")
            pass
        except psycopg2.InterfaceError as e:
            print(e)
            print("Retrying...")
            pass
        except psycopg2.DatabaseError as e:
            print(e)
            print("Retrying...")
            pass
        except psycopg2.OperationalError as e:
            print(e)
            print("Retrying...")
            pass


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


def write_dframe_direct(dframe, url, table, if_exists="append", index=True):
    engine = init_engine(url)
    dframe.to_sql(table, engine, if_exists=if_exists, index=index)


def write_dframe_copy_from(dframe, url, table, index=False, num_retries=3):
    """ COPY FROM a csv is often MUCH faster than dframe.to_sql """

    if index:
        dframe = dframe.reset_index()

    temp_file = tempfile.NamedTemporaryFile()
    local.write_dframe(dframe, temp_file.name, index=False, header=False)
    clean_file_floats(temp_file.name)
    columns = list(str(c) for c in dframe.columns)

    for i in range(num_retries):
        try:
            copy_from_fname(temp_file.name, table, columns=columns, url=url)
            break
        except sa.exc.DatabaseError as e:
            # connection likely stale, retrying...
            print(e)
            print("Retrying...")
            pass
        except psycopg2.InterfaceError as e:
            print(e)
            print("Retrying...")
            pass
        except psycopg2.DatabaseError as e:
            print(e)
            print("Retrying...")
            pass
        except psycopg2.OperationalError as e:
            print(e)
            print("Retrying...")
            pass


def copy_from_fname(fname, table, columns=None, conn=None, url=None):
    assert url is not None or conn is not None, "need conn or url specified"

    commit = conn is None
    if conn is None:
        engine = init_engine(url)
        conn = engine.raw_connection()

    with conn.cursor() as cur:
        with open(fname) as f:
            cur.copy_from(f, table, sep=",", null="", columns=columns)

    if commit:
        conn.commit()
        conn.close()


def write_dframes_copy_from(dframes, url, tables, index=False):
    """ Write multiple tables as a single transaction. """
    assert len(dframes) == len(tables)
    engine = init_engine(url)

    conn = engine.raw_connection()
    temp_file = tempfile.NamedTemporaryFile()
    for (dframe, table) in zip(dframes, tables):

        if index:
            dframe = dframe.reset_index()

        local.write_dframe(dframe, temp_file.name, index=False, header=False)
        clean_file_floats(temp_file.name)
        columns = list(str(c) for c in dframe.columns)

        copy_from_fname(temp_file.name, table, columns=columns, conn=conn)

    conn.commit()
    conn.close()


def clean_file_floats(fname):
    temp_file = tempfile.NamedTemporaryFile()

    with open(fname) as f:
        with open(temp_file.name, "w+") as f2:
            for line in f:
                f2.write(line.replace(".0", ""))

    shutil.copy(temp_file.name, fname)


def create_index(url, tablename, *colnames):
    engine = init_engine(url)

    metadata = open_db_metadata(url)
    columns = [metadata.tables[tablename].c[colname] for colname in colnames]
    colstring = "_".join(colnames)

    index = sa.Index(f"manual_idx_{tablename}_{colstring}", *columns)

    index.create(engine)
