from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from src.utils import *
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Optional
from dataclasses import dataclass
from src.models import SqlImprovementState, SchemaInfo
from src.bq_client import BigQueryClient


class SqlAnalyzer:
    def __init__(self, llm: ChatGoogleGenerativeAI, bq_client: BigQueryClient):
        self.llm = llm
        self.bq_client = bq_client
        pass

    def get_table_info(self, state: SqlImprovementState) -> SqlImprovementState:
        """First Improvement"""
        msg = self.llm.invoke(get_table_schema_prompt(state["sql"]))
        tables = []
        for table in msg.content.split(", "):
            metadata = self.bq_client.get_table_metadata(table)
            tables.append(metadata)

        return {"tabels": tables}

    def generate_info(self, state: SqlImprovementState) -> SqlImprovementState:
        """First Improvement"""
        msg = self.llm.invoke(get_antipatterns_prompt(state["sql"]))
        antipatterns = []
        current_pattern = {}
        for line in msg.content.split("\n"):
            if not line:
                if current_pattern:
                    antipatterns.append(current_pattern)
                    current_pattern = {}
                continue
            line = line.strip()
            line = line.replace("*", "")
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().upper()
                value = value.strip()
                if key in ["CODE", "NAME", "DESCRIPTION", "IMPACT", "LOCATION", "SUGGESTION"]:
                    current_pattern[key.lower()] = value
        if current_pattern:
            antipatterns.append(current_pattern)
        return {"antipattterns": antipatterns}

    def get_previous_optimizations(self, state: SqlImprovementState) -> SqlImprovementState:
        return {}

    def get_suggestions(self, state: SqlImprovementState) -> SqlImprovementState:
        """Get optimization suggestions using a focused prompt."""
        try:
            msg = self.llm.invoke(
                get_suggestions_prompt(state["sql"], state["antipattterns"], state["tabels"])
            )
            # Extract suggestions (lines starting with '- ')
            print(msg.content)
            suggestions = []
            for line in msg.content.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    suggestions.append(line[2:])
            return {"improvements": [msg.content]}

        except Exception as e:
            print(f"Error getting suggestions: {str(e)}")
            return {"improvements": []}

    def get_optimized_query(self, state: SqlImprovementState) -> SqlImprovementState:
        return {}

    def loca_performance_test(self, state: SqlImprovementState) -> SqlImprovementState:
        return {}
