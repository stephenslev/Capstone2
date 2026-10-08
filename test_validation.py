from agents import quantitative
from validation.validator import (
    validate_qualitative,
    validate_quantitative,
)


def test_qualitative_failure() -> None:
    irrelevant_chunks = [
        {
            "source": "customer-complaints-policy.txt",
            "chunk": 0,
            "content": "Customer complaints are logged and reviewed.",
        }
    ]

    bad_answer = (
        "Every production code change requires two reviewers."
    )

    result = validate_qualitative(
        answer=bad_answer,
        chunks=irrelevant_chunks,
    )

    assert result["flag"] is True, result
    print("Qualitative failure flagged:", result)


def fake_generate_sql(query: str) -> dict:
    return {
        "sql": "DELETE FROM sales",
        "input_tokens": 0,
        "output_tokens": 0,
    }


def test_quantitative_failure() -> None:
    sql = "DELETE FROM sales"

    sql_check = quantitative.validate_sql(sql)
    assert sql_check["valid"] is False, sql_check

    validation = validate_quantitative(
        answer="",
        sql=sql,
        validation_status="FAILED",
    )
    assert validation["flag"] is True, validation

    original_generate_sql = quantitative.generate_sql
    quantitative.generate_sql = fake_generate_sql

    try:
        result = quantitative.run("Delete all sales records")
    finally:
        quantitative.generate_sql = original_generate_sql

    assert result["validation"] == "FAILED", result
    assert result["rows"] == [], result

    print("Quantitative failure flagged:", validation)
    print("SQL execution prevented:", result)


if __name__ == "__main__":
    test_qualitative_failure()
    test_quantitative_failure()
    print("All validation checkpoint tests passed.")
