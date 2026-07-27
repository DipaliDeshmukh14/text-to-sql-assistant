import os
import uuid
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

# We use this same local Postgres server as scratch space for uploaded CSVs.
# Each upload gets its own uniquely-named table so uploads never collide.
BASE_DB_URL = os.getenv("DATABASE_URL")


def load_csv_to_table(file_path: str, original_filename: str) -> str:
    """
    Reads a CSV, creates a fresh table named after the file, and loads
    the data into it. Returns the table name so we can tell the user
    what to reference (though the schema introspection will find it too).
    """
    df = pd.read_csv(file_path)

    # Sanitize table name: letters/numbers/underscores only, must start with a letter
    base_name = os.path.splitext(original_filename)[0].lower()
    safe_name = "".join(c if c.isalnum() else "_" for c in base_name)
    table_name = f"upload_{safe_name}_{uuid.uuid4().hex[:6]}"

    engine = create_engine(BASE_DB_URL)
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    engine.dispose()

    return table_name


def load_sql_file(file_path: str):
    """
    Runs a raw .sql file (schema + data) against the same scratch database.
    Lets users upload their own schema.sql-style dump directly.
    """
    engine = create_engine(BASE_DB_URL)
    with open(file_path, "r") as f:
        sql_script = f.read()

    with engine.connect() as conn:
        for statement in sql_script.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(statement + ";")
        conn.commit()
    engine.dispose()


def test_connection(db_url: str) -> bool:
    """Quick check that a user-provided connection URL actually works."""
    try:
        engine = create_engine(db_url)
        with engine.connect():
            pass
        engine.dispose()
        return True
    except Exception:
        return False