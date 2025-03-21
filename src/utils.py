from src.constants import SQL_ANTIPATTERNS
from typing import Optional
from src.models import SqlImprovementState, SchemaInfo
import json


def get_table_schema_prompt(query: str) -> str:
    prompt = f"""Extract all table names from the following SQL query. Return the table names as a comma-separated list.

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
    query: str, antipatterns: list[str] = None, schema_info: Optional[list[SchemaInfo]] = None
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
            f"{ap.get('code', 'UNKNOWN')}: {ap.get('name', '')} - {ap.get('description', '')} (Impact: {ap.get('impact', 'Unknown')})"
            for ap in antipatterns
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

    print()
    print(suggestion_prompt)
    print()

    return antipatterns_prompt
