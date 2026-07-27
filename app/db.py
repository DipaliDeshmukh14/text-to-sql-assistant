import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

active_db_url = os.getenv("DATABASE_URL")
# When someone uploads a file, we restrict the LLM's view to just that
# table (or set of tables) instead of the whole database — avoids
# ambiguous matches like a demo table also having a "city" column.
active_table_filter = None


def set_active_db(url: str):
    global active_db_url, active_table_filter
    active_db_url = url
    active_table_filter = None  # connecting to a new DB shows everything in it


def set_active_table(table_name: str):
    global active_table_filter
    active_table_filter = table_name


def clear_table_filter():
    global active_table_filter
    active_table_filter = None


def get_connection(db_url: str = None):
    return psycopg2.connect(db_url or active_db_url)


def get_schema_text(db_url: str = None) -> str:
    query = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """
    conn = get_connection(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
    finally:
        conn.close()

    tables = {}
    for table_name, column_name, data_type in rows:
        if active_table_filter and table_name != active_table_filter:
            continue
        tables.setdefault(table_name, []).append(f"{column_name} ({data_type})")

    return "\n".join(f"Table {t}: " + ", ".join(cols) for t, cols in tables.items())


def run_select_query(sql: str, db_url: str = None, limit: int = 200):
    conn = get_connection(db_url)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchmany(limit)
            columns = [d[0] for d in cur.description] if cur.description else []
            return columns, [dict(r) for r in rows]
    finally:
        conn.close()