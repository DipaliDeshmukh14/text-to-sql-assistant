import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SQL_SYSTEM_PROMPT = """You are a PostgreSQL expert. Convert the user's question into a single valid PostgreSQL SELECT query.

Here is the database schema:
{schema}

Recent conversation (most recent last):
{history}

Rules:
- Only output the raw SQL query, nothing else. No explanation, no markdown.
- Only generate SELECT statements. Never modify data.
- Use only the tables and columns listed above.
- IMPORTANT: If the current question is short, vague, or refers to "that", "those", "what about X" — it is a FOLLOW-UP to the most recent question in the conversation above. Reuse that previous query's structure (same SELECT/aggregation/table), and only change the specific value being filtered on (e.g. if the last query filtered department = 'Engineering' and the new question is "what about Sales?", change the filter to department = 'Sales').
- Only say a question cannot be answered if it truly has no relation to the schema or conversation — never default to "cannot answer" just because the question alone seems incomplete.
- If the question is a greeting, small talk, or unrelated to data (e.g. "hi", "how are you", "let's talk"), output exactly: SELECT 'CHAT' AS mode;
- If the question genuinely cannot be answered with the given schema, output: SELECT 'Cannot answer with available data' AS message;
"""

EXPLAIN_SYSTEM_PROMPT = """Explain what this SQL query does in one or two short, plain-English sentences.
No jargon, no repeating the SQL back. Write for someone who doesn't know SQL."""


def generate_sql(question: str, schema: str, history: list) -> str:
    history_text = "\n".join(
        f"Q: {h['question']}\nSQL: {h['sql']}" for h in history[-3:]  # last 3 turns only
    ) or "None yet — this is the first question."

    system_prompt = SQL_SYSTEM_PROMPT.format(schema=schema, history=history_text)

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=0,
    )
    return response.choices[0].message.content.strip()


def explain_sql(sql: str) -> str:
    response = client.chat.completions.create(
         model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": EXPLAIN_SYSTEM_PROMPT},
            {"role": "user", "content": sql},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def fix_sql(question: str, schema: str, broken_sql: str, error_message: str) -> str:
    """Self-correction: if execution failed, ask the LLM to fix its own query."""
    prompt = f"""This SQL query failed to run:
{broken_sql}

Error: {error_message}

Original question: {question}
Schema:
{schema}

Output ONLY the corrected SQL query, nothing else."""

    response = client.chat.completions.create(
         model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a PostgreSQL expert fixing a broken query."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    return response.choices[0].message.content.strip()