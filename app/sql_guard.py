import re

BLOCKED_KEYWORDS = [
    "insert", "update", "delete", "drop", "alter", "truncate",
    "create", "grant", "revoke", "--", "/*", "xp_cmdshell",
]


class UnsafeQueryError(Exception):
    pass


def clean_sql(raw: str) -> str:
    """Strip markdown fences the LLM sometimes wraps SQL in."""
    sql = raw.strip()
    sql = re.sub(r"^```(sql)?", "", sql, flags=re.IGNORECASE).strip()
    sql = re.sub(r"```$", "", sql).strip()
    sql = sql.split(";")[0].strip() + ";"  # only first statement, no stacked queries
    return sql


def validate_select_only(sql: str) -> str:
    cleaned = clean_sql(sql)
    lowered = cleaned.lower()

    if not lowered.lstrip().startswith("select"):
        raise UnsafeQueryError("Only SELECT queries are allowed.")

    for keyword in BLOCKED_KEYWORDS:
        if keyword in lowered:
            raise UnsafeQueryError(f"Query contains a disallowed keyword: '{keyword}'")

    return cleaned