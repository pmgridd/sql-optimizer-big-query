from src.common.constants import SQL_ANTIPATTERNS
from typing import Optional
from src.lgraph.models import SqlImprovementState, SchemaInfo


def get_table_schema_prompt(query: str) -> str:
    prompt = f"""
Extract all table names from the following SQL query.
Return the fully-qualified table names in the format 'project.dataset.table_id' as a comma-separated list.
If no tables found - return 'no_tables_found'.

SQL Query: {query}

Table Names:
"""
    return prompt


def get_antipatterns_prompt(query: str) -> str:
    """Get antipatterns using a focused prompt."""
    antipattern_codes = ""
    for category, antipatterns in SQL_ANTIPATTERNS.items():
        for a_code, a_object in antipatterns.items():
            a_name = a_object["name"]
            antipattern_codes += f"{category}:{a_code} ({a_name})\n"
    antipattern_prompt = f"""Analyze this SQL query for antipatterns.
For each antipattern found, provide the following information in plain text format:
```
CODE: (use only one from the list below, don't use any other)
NAME: (name of the antipattern)
DESCRIPTION: (brief description)
IMPACT: (High, Medium, or Low)
LOCATION: (where in query)
SUGGESTION: (how to fix)
```
Available codes:
{antipattern_codes}

Query to analyze:
{query}
        """
    # print()
    # print(antipattern_prompt)
    # print()
    return antipattern_prompt


def get_suggestions_prompt(
    query: str, antipatterns: list[dict] = None, schema_info: Optional[list[SchemaInfo]] = None
) -> str:
    schema_context = ""
    if schema_info:
        for info in schema_info:
            # print(print(json.dumps(info, indent=4)))
            schema_context += (
                f"The Query uses the following Table\n"
                f"Table: {info['table_name']}\n"
                f"Row Count: {info['row_count']}\n"
                f"Table Size in Bytes: {info['size_bytes']}\n"
                "| COLUMN_NAME | COLUMN_TYPE |\n"
                "| ----------- | ----------- |\n"
            )
            for column in info["columns"]:
                schema_context += f"| {column['column_name']} | {column['column_type']} |\n"
    else:
        schema_context = ""
    if antipatterns is not None:
        antipatterns_str = [
            f"{ap.get('code', 'UNKNOWN')}: {ap.get('name', '')}" for ap in antipatterns
        ]
        antipatterns_prompt = "The query contains the following antipatterns:\n" + "\n".join(
            antipatterns_str
        )
    else:
        antipatterns_prompt = ""
    suggestion_prompt = f"""
Analyze this SQL query and suggest optimizations.
Provide each suggestion on a new line starting with '- '.
Focus on query structure and BigQuery features.
Keep each suggestion brief and focused, without excessive language.

Query to analyze:
    {query}

{schema_context.lstrip()}

{antipatterns_prompt}

""".lstrip()
    return suggestion_prompt


def get_optimized_sql_prompt(
    query: str,
    improvements: list[str] = None,
    antipatterns: list[dict] = None,
    schema_info: Optional[list[SchemaInfo]] = None,
) -> str:
    schema_context = ""
    if schema_info:
        for info in schema_info:
            schema_context += (
                f"The Query uses the following Table\n"
                f"Table: {info['table_name']}\n"
                f"Row Count: {info['row_count']}\n"
                f"Table Size in Bytes: {info['size_bytes']}\n"
                "| COLUMN_NAME | COLUMN_TYPE |\n"
                "| ----------- | ----------- |\n"
            )
            for column in info["columns"]:
                schema_context += f"| {column['column_name']} | {column['column_type']} |\n"
    else:
        schema_context = ""
    if antipatterns is not None:
        antipatterns_str = [
            f"{ap.get('code', 'UNKNOWN')}: {ap.get('name', '')}" for ap in antipatterns
        ]
        antipatterns_prompt = "The query contains the following antipatterns:\n" + "\n".join(
            antipatterns_str
        )
    else:
        antipatterns_prompt = ""

    if improvements is not None:
        improvements_prompt = "The query contains the following suggestions:\n" + "\n".join(
            improvements
        )
    else:
        improvements_prompt = ""
    # {improvements_prompt}
    suggestion_prompt = f"""
Analyze this SQL query and provide optimized SQL based on antipatterns and provided table information.
Query to analyze:
    {query}

{antipatterns_prompt}



{schema_context.lstrip()}

Provide optimized SQL in the form of new SQL query, no comments and old version of the query is needed:
""".lstrip()

    return suggestion_prompt


def evaluate_query(results: dict) -> dict:
    score = 0
    weights = {
        "execution_time_seconds": 0.40,
        "total_bytes_processed": 0.30,
        "total_bytes_billed": 0.15,
        "cache_hit": 0.10,
        "num_dml_affected_rows": 0.05,
    }
    score += (1 / (1 + results["execution_time_seconds"])) * weights["execution_time_seconds"]
    score += (1 / (1 + results["total_bytes_processed"])) * weights["total_bytes_processed"]
    score += (1 / (1 + results["total_bytes_billed"])) * weights["total_bytes_billed"]
    score += (1 if results["cache_hit"] else 0) * weights["cache_hit"]
    score += (results["num_dml_affected_rows"] / 1000) * weights["num_dml_affected_rows"]
    return {"score": score, "metadata": results}


def get_optimized_sql_prompt2(
    query: str,
    improvements: list[str] = None,
    antipatterns: list[dict] = None,
    schema_info: Optional[list[SchemaInfo]] = None,
) -> str:
    schema_context = ""
    if schema_info:
        for info in schema_info:
            schema_context += (
                f"The Query uses the following Table\n"
                f"Table: {info['table_name']}\n"
                f"Row Count: {info['row_count']}\n"
                f"Table Size in Bytes: {info['size_bytes']}\n"
                "| COLUMN_NAME | COLUMN_TYPE |\n"
                "| ----------- | ----------- |\n"
            )
            for column in info["columns"]:
                schema_context += f"| {column['column_name']} | {column['column_type']} |\n"
    else:
        schema_context = ""
    if antipatterns is not None:
        antipatterns_str = [
            f"{ap.get('code', 'UNKNOWN')}: {ap.get('name', '')}" for ap in antipatterns
        ]
        antipatterns_prompt = "The query contains the following antipatterns:\n" + "\n".join(
            antipatterns_str
        )
    else:
        antipatterns_prompt = ""

    if improvements is not None:
        improvements_prompt = "The query contains the following suggestions:\n" + "\n".join(
            improvements
        )
    else:
        improvements_prompt = ""
    # {improvements_prompt}
    suggestion_prompt = f"""
Analyze this SQL query and provide optimized SQL based on antipatterns and provided table information. If table information is not available or empty - don't try to invent the columns, use available data or *
Query to analyze:
    {query}

{antipatterns_prompt}



{schema_context.lstrip()}

Provide optimized SQL in the form of new SQL query, no comments and old version of the query is needed:
""".lstrip()

    return suggestion_prompt
