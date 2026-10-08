# filename: agents/manager.py

import os

from dotenv import load_dotenv
from openai import OpenAI

from agents import qualitative, quantitative
from tokenomics.logger import log
from validation.validator import (
    validate_qualitative,
    validate_quantitative,
)

load_dotenv()

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from the .env file")

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

ALLOWED_ROUTES = {"qualitative", "quantitative", "both"}

DEBUG_VALIDATION = os.getenv("VALIDATION_DEBUG", "false").lower() in {
    "1",
    "true",
    "yes",
}


def print_validation_result(label: str, validation: dict) -> None:
    status = "FLAGGED" if validation.get("flag") else "PASSED"

    print(f"\n[{label} validation: {status}]")

    for key, value in validation.items():
        print(f"  {key}: {value}")


def print_debug_output(label: str, output: str) -> None:
    if DEBUG_VALIDATION:
        print(f"\n[DEBUG] {label} captured before validation:")
        print(output)


def get_usage(response) -> tuple[int, int]:
    usage = getattr(response, "usage", None)

    if usage is None:
        return 0, 0

    return (
        int(getattr(usage, "prompt_tokens", 0) or 0),
        int(getattr(usage, "completion_tokens", 0) or 0),
    )


def classify(query: str) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0,
        max_tokens=10,
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify each query as exactly one of: "
                    "qualitative, quantitative, or both. "
                    "Reply with one word only."
                ),
            },
            {
                "role": "user",
                "content": (
                    "qualitative = policies, processes, procedures, "
                    "explanations, or documentation\n"
                    "quantitative = numbers, metrics, trends, "
                    "comparisons, or SQL-queryable data\n"
                    "both = requires document search and data analysis\n\n"
                    f"Query: {query}\n\n"
                    "Reply with one word only: qualitative, "
                    "quantitative, or both."
                ),
            },
        ],
    )

    raw_route = response.choices[0].message.content or ""
    route = raw_route.strip().lower().strip(".,`")
    input_tokens, output_tokens = get_usage(response)

    log(query, "manager-classifier", input_tokens, output_tokens)

    return route if route in ALLOWED_ROUTES else "qualitative"


def create_combined_overview(
    query: str,
    qualitative_answer: str,
    quantitative_answer: str,
    sql: str,
) -> tuple[str, int, int]:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0.2,
        max_tokens=700,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an enterprise analysis synthesizer. "
                    "Use only the two validated outputs provided. "
                    "Combine the qualitative policy findings with the "
                    "quantitative results into one concise overview. "
                    "Do not invent facts or use outside knowledge. "
                    "Preserve citations such as [Source 1]. "
                    "Do not claim causation unless the evidence explicitly "
                    "supports it. Clearly identify missing information, "
                    "limitations, or differences between the two outputs."
                ),
            },
            {
                "role": "user",
                "content": f"""
QUESTION:
{query}

VALIDATED QUALITATIVE RESULT:
{qualitative_answer}

VALIDATED QUANTITATIVE RESULT:
{quantitative_answer}

SQL USED:
{sql}

Create an overview with:
1. Key quantitative findings
2. Relevant policies or qualitative context
3. How the two findings relate
4. Important limitations or missing evidence
""",
            },
        ],
    )

    overview = response.choices[0].message.content or ""
    input_tokens, output_tokens = get_usage(response)

    return overview, input_tokens, output_tokens


def run(query: str) -> None:
    print(f"\nQuery: {query}")

    route = classify(query)
    print(f"Route: {route}")

    qualitative_result = None
    quantitative_result = None
    qualitative_validation = None
    quantitative_validation = None

    if route in {"qualitative", "both"}:
        qualitative_result = qualitative.run(query)

        print_debug_output(
            "Qualitative model answer",
            qualitative_result["answer"],
        )

        qualitative_validation = validate_qualitative(
            qualitative_result["answer"],
            qualitative_result["chunks"],
        )

        print_validation_result(
            "Qualitative",
            qualitative_validation,
        )

        log(
            query,
            "qualitative",
            qualitative_result["input_tokens"],
            qualitative_result["output_tokens"],
        )

        if qualitative_validation["flag"]:
            print(f"\nWARNING: {qualitative_validation['warning']}")
            print(
                "\n[Qualitative]\n"
                "Response withheld because validation failed."
            )
        else:
            print(f"\n[Qualitative]\n{qualitative_result['answer']}")

    if route in {"quantitative", "both"}:
        quantitative_result = quantitative.run(query)

        print_debug_output(
            "Generated SQL",
            quantitative_result["sql"],
        )

        quantitative_validation = validate_quantitative(
            quantitative_result["answer"],
            quantitative_result["sql"],
            quantitative_result["validation"],
        )

        print_validation_result(
            "Quantitative",
            quantitative_validation,
        )

        log(
            query,
            "quantitative",
            quantitative_result["input_tokens"],
            quantitative_result["output_tokens"],
        )

        if quantitative_validation["flag"]:
            print(f"\nWARNING: {quantitative_validation['warning']}")
            print(
                "\n[Quantitative]\n"
                "Response withheld because validation failed."
            )
        else:
            print(f"\n[Quantitative]\n{quantitative_result['answer']}")
            print(f"SQL used: {quantitative_result['sql']}")

    if route == "both":
        inputs_are_valid = (
            qualitative_validation is not None
            and quantitative_validation is not None
            and not qualitative_validation["flag"]
            and not quantitative_validation["flag"]
        )

        if not inputs_are_valid:
            print(
                "\n[Combined overview]\n"
                "Overview withheld because one or more agent results "
                "failed validation."
            )
            return

        overview, input_tokens, output_tokens = create_combined_overview(
            query,
            qualitative_result["answer"],
            quantitative_result["answer"],
            quantitative_result["sql"],
        )

        print_debug_output("Combined overview", overview)

        log(
            query,
            "combined-overview",
            input_tokens,
            output_tokens,
        )

        print(f"\n[Combined overview]\n{overview}")
