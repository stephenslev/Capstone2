import os
import re
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "database.sqlite"
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from the .env file")

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

SCHEMA_CONTEXT = """
Available SQLite tables and views:

monthly_revenue(
    month, region, revenue, target_revenue
)

customer_metrics(
    month, region, active_customers, new_customers,
    churned_customers, churn_rate, nps_score
)

regional_performance(
    quarter, region, revenue, target_revenue,
    new_customers, renewal_rate, win_rate
)

employee_satisfaction(
    period, department, satisfaction_score,
    industry_benchmark, response_count
)

employee_policy_metrics(
    period, policy_name, adoption_rate,
    employee_satisfaction_score, industry_benchmark
)

sales_performance(
    month, region, qualified_opportunities, closed_won,
    win_rate, sales_revenue, average_deal_size
)

customer_success_metrics(
    month, region, active_accounts, at_risk_accounts,
    renewal_rate, adoption_rate, avg_resolution_hours
)

monthly_revenue_trend(
    month, total_revenue, total_target_revenue, attainment_rate
)

customer_churn_summary(
    month, active_customers, churned_customers, churn_rate
)

q4_regional_comparison(
    region, revenue, target_revenue, attainment_rate,
    new_customers, renewal_rate, win_rate
)

Compatibility tables:

sales(
    id, region, product, revenue, date, units_sold,
    qualified_opportunities, closed_won, win_rate,
    renewal_rate, adoption_rate, at_risk_accounts,
    avg_resolution_hours
)

customers(
    id, name, industry, region, churn_date,
    satisfaction_score, status
)

employees(
    id, department, satisfaction_score,
    tenure_years, period, industry_benchmark
)
"""

BLOCKED_KEYWORDS = {
    "DROP",
    "DELETE",
    "UPDATE",
    "INSERT",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "REPLACE",
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "VACUUM",
    "REINDEX",
}


def get_usage(response) -> tuple[int, int]:
    usage = getattr(response, "usage", None)

    if usage is None:
        return 0, 0

    input_tokens = int(
        getattr(usage, "prompt_tokens", 0) or 0
    )
    output_tokens = int(
        getattr(usage, "completion_tokens", 0) or 0
    )

    return input_tokens, output_tokens


def clean_sql(sql: str) -> str:
    cleaned = sql.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    return cleaned.rstrip(";").strip()


def validate_sql(query: str) -> dict:
    sql = query.strip()

    if not sql:
        return {
            "valid": False,
            "reason": "The generated SQL was empty",
        }

    if not re.match(r"^(SELECT|WITH)\b", sql, re.IGNORECASE):
        return {
            "valid": False,
            "reason": "Only SELECT or read-only WITH queries are permitted",
        }

    if ";" in sql:
        return {
            "valid": False,
            "reason": "Multiple SQL statements are not permitted",
        }

    if "--" in sql or "/*" in sql or "*/" in sql:
        return {
            "valid": False,
            "reason": "SQL comments are not permitted",
        }

    for keyword in BLOCKED_KEYWORDS:
        pattern = rf"\b{keyword}\b"

        if re.search(pattern, sql, re.IGNORECASE):
            return {
                "valid": False,
                "reason": f"Blocked keyword: {keyword}",
            }

    return {
        "valid": True,
        "reason": "OK",
    }


def generate_sql(query: str) -> dict:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0,
        max_tokens=256,
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate safe, read-only SQLite queries. "
                    "Use only the tables and columns in the supplied schema. "
                    "Never invent tables or columns. "
                    "Return only one SELECT or read-only WITH query. "
                    "Do not include markdown fences or explanations."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{SCHEMA_CONTEXT}\n\n"
                    f"User question:\n{query}\n\n"
                    "Generate the SQL query now."
                ),
            },
        ],
    )

    raw_sql = response.choices[0].message.content or ""
    input_tokens, output_tokens = get_usage(response)

    return {
        "sql": clean_sql(raw_sql),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


def interpret_results(
    query: str,
    sql: str,
    columns: list[str],
    rows: list[tuple],
) -> dict:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0.2,
        max_tokens=512,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a quantitative analysis assistant. "
                    "Interpret only the SQL results provided. "
                    "Do not invent facts or metrics. "
                    "Clearly distinguish observations from conclusions."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User question:\n{query}\n\n"
                    f"SQL query used:\n{sql}\n\n"
                    f"Result columns:\n{columns}\n\n"
                    f"Result rows:\n{rows[:20]}\n\n"
                    "Provide a clear, concise interpretation."
                ),
            },
        ],
    )

    answer = response.choices[0].message.content or ""
    input_tokens, output_tokens = get_usage(response)

    return {
        "answer": answer,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


def run(query: str) -> dict:
    sql_result = generate_sql(query)
    sql = sql_result["sql"]
    validation = validate_sql(sql)

    if not validation["valid"]:
        return {
            "answer": f"Query blocked: {validation['reason']}",
            "sql": sql,
            "rows": [],
            "validation": "FAILED",
            "input_tokens": sql_result["input_tokens"],
            "output_tokens": sql_result["output_tokens"],
        }

    if not DATABASE_PATH.exists():
        return {
            "answer": f"Database not found: {DATABASE_PATH}",
            "sql": sql,
            "rows": [],
            "validation": "ERROR",
            "input_tokens": sql_result["input_tokens"],
            "output_tokens": sql_result["output_tokens"],
        }

    try:
        with sqlite3.connect(str(DATABASE_PATH)) as connection:
            cursor = connection.execute(sql)
            rows = cursor.fetchall()
            columns = [
                description[0]
                for description in cursor.description or []
            ]

        interpretation = interpret_results(
            query=query,
            sql=sql,
            columns=columns,
            rows=rows,
        )

        return {
            "answer": interpretation["answer"],
            "sql": sql,
            "columns": columns,
            "rows": rows,
            "validation": "PASSED",
            "input_tokens": (
                sql_result["input_tokens"]
                + interpretation["input_tokens"]
            ),
            "output_tokens": (
                sql_result["output_tokens"]
                + interpretation["output_tokens"]
            ),
        }

    except Exception as error:
        return {
            "answer": f"Query execution failed: {error}",
            "sql": sql,
            "rows": [],
            "validation": "ERROR",
            "input_tokens": sql_result["input_tokens"],
            "output_tokens": sql_result["output_tokens"],
        }

