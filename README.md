# Text-to-SQL Assistant

Ask your database questions in plain English — get back the exact SQL query and the answer. Built as a full-stack project exploring natural language interfaces to structured data.

## Features
- Natural language → SQL using Groq (Llama 3.3 70B)
- Safety layer: only SELECT queries allowed, blocks INSERT/UPDATE/DELETE/DROP etc.
- Bring your own data: connect a live Postgres URL or upload a .csv/.sql file
- Multi-turn conversation memory — follow-up questions like "what about Sales?" work
- Plain-English explanation alongside every generated query
- Self-correcting: retries once if the generated SQL fails to execute
- Dynamic schema introspection — no hardcoded table/column names

## Tech Stack
**Backend:** FastAPI · PostgreSQL · Groq API · psycopg2 · SQLAlchemy · pandas
**Frontend:** React (Vite)

## Setup

### Backend
1. `cd text-to-sql`
2. `python3 -m venv venv && source venv/bin/activate`
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`, add your Groq API key and database URL
5. Create the database and load sample data:

6. Run: `uvicorn app.main:app --reload`

### Frontend
1. `cd text-to-sql-frontend`
2. `npm install`
3. `npm run dev`
4. Visit `http://localhost:5173`

## Example
**Question:** "Which customer has spent the most money?"
**Generated SQL:** Auto-generated JOIN across customers, orders, order_items, products
**Answer:** Top-spending customer, by name

## Architecture
Follow-up questions retain the last few turns of conversation so context like "what about X?" resolves correctly.