import shutil
import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.db import get_schema_text, run_select_query, set_active_db, set_active_table
from app.llm import generate_sql, explain_sql, fix_sql
from app.sql_guard import validate_select_only, UnsafeQueryError
from app.user_db import load_csv_to_table, load_sql_file, test_connection

app = FastAPI(title="Text-to-SQL Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory conversation history — fine for a single-user demo.
# Resets whenever the server restarts.
conversation_history = []


class QueryRequest(BaseModel):
    question: str


class ConnectRequest(BaseModel):
    db_url: str


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Text-to-SQL Assistant is running"}


@app.post("/reset")
def reset_conversation():
    """Clears chat history — call this when the user starts a new chat."""
    conversation_history.clear()
    return {"status": "reset"}


@app.post("/connect")
def connect_database(request: ConnectRequest):
    if not test_connection(request.db_url):
        raise HTTPException(status_code=400, detail="Could not connect. Check your connection URL.")
    set_active_db(request.db_url)
    conversation_history.clear()
    schema = get_schema_text()
    return {"status": "connected", "schema_preview": schema}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        if file.filename.endswith(".csv"):
            table_name = load_csv_to_table(temp_path, file.filename)
            set_active_table(table_name)
            message = f"Loaded into table '{table_name}'"
        elif file.filename.endswith(".sql"):
            load_sql_file(temp_path)
            message = "SQL file executed successfully"
        else:
            raise HTTPException(status_code=400, detail="Only .csv or .sql files are supported.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load file: {e}")
    finally:
        os.remove(temp_path)

    conversation_history.clear()
    schema = get_schema_text()
    return {"status": "loaded", "message": message, "schema_preview": schema}


@app.post("/query")
def query(request: QueryRequest):
    schema = get_schema_text()
    raw_sql = generate_sql(request.question, schema, conversation_history)

    try:
        safe_sql = validate_select_only(raw_sql)
        if "'CHAT' AS mode" in safe_sql:
            return {
            "question": request.question,
            "generated_sql": None,
            "explanation": "Hi! I'm here to help you explore your data — ask me a question about it, like \"how many rows are in X\" or \"what's the average Y by Z\".",
            "columns": [],
            "results": [],
        }
    except UnsafeQueryError as e:
        raise HTTPException(status_code=400, detail=f"Blocked unsafe query: {e}")

    try:
        columns, rows = run_select_query(safe_sql)
    except Exception as first_error:
        # Self-correction: give the LLM one chance to fix its own broken query
        try:
            fixed_raw = fix_sql(request.question, schema, safe_sql, str(first_error))
            safe_sql = validate_select_only(fixed_raw)
            columns, rows = run_select_query(safe_sql)
        except Exception as second_error:
            raise HTTPException(status_code=400, detail=f"SQL execution failed: {second_error}")

    explanation = explain_sql(safe_sql)

    conversation_history.append({"question": request.question, "sql": safe_sql})

    return {
        "question": request.question,
        "generated_sql": safe_sql,
        "explanation": explanation,
        "columns": columns,
        "results": rows,
    }