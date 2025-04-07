from src.common.utils import *
from langchain_google_genai import ChatGoogleGenerativeAI
from src.lgraph.models import SqlImprovementState
from src.lgraph.bq_client import BigQueryClient
import asyncio
import logging
import random

logger = logging.getLogger(__name__)


class SqlAnalyzer:
    def __init__(self, llm: ChatGoogleGenerativeAI, bq_client: BigQueryClient):
        self.llm = llm
        self.bq_client = bq_client

    async def get_table_info(self, state: SqlImprovementState) -> SqlImprovementState:
        """First Improvement"""

        async def fetch_metadata(table):
            return await asyncio.to_thread(self.bq_client.get_table_metadata, table)

        msg = await self.llm.ainvoke(get_table_schema_prompt(state["sql"]))
        if "no_tables_found" not in msg.content.strip():
            tables = await asyncio.gather(
                *(fetch_metadata(table.strip()) for table in msg.content.split(","))
            )
            return {"tabels": tables}
        else:
            raise RuntimeError("No tables found in the provided SQL query.")  # no retry by default

    async def generate_info(self, state: SqlImprovementState) -> SqlImprovementState:
        """First Improvement"""
        msg = await self.llm.ainvoke(get_antipatterns_prompt(state["sql"]))
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
        return {"antipatterns": antipatterns}

    async def get_previous_optimizations(self, state: SqlImprovementState) -> SqlImprovementState:
        return {}

    async def get_suggestions(self, state: SqlImprovementState) -> SqlImprovementState:
        """Get optimization suggestions using a focused prompt."""
        try:
            msg = await self.llm.ainvoke(
                get_suggestions_prompt(state["sql"], state["antipatterns"], state["tables"])
            )
            suggestions = []
            for line in msg.content.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    suggestions.append(line[2:])
            return {"improvements": suggestions}

        except Exception as e:
            print(f"Error getting suggestions: {str(e)}")
            return {"improvements": []}

    async def get_optimized_query(self, state: SqlImprovementState) -> SqlImprovementState:
        """Get optimization suggestions using a focused prompt."""
        try:
            msg = await self.llm.ainvoke(
                get_optimized_sql_prompt(state["sql"], state["antipatterns"], state["tables"])
            )

            def clean_sql_string(sql_string):
                return sql_string.replace("```sql", "").replace("```", "").strip()

            return {"optimized_sql": clean_sql_string(msg.content)}

        except Exception as e:
            print(f"Error getting suggestions: {str(e)}")
            return {"optimized_sql": ""}

    async def verify_and_run_original_sql(self, state: SqlImprovementState) -> SqlImprovementState:
        if random.random() < 0.6:  # 60% chance of failure
            raise Exception("Simulated BigQuery query failure")  # retry 3 times by default
        res = self.bq_client.execute_sql_query(state["sql"])
        return {"sql_res": evaluate_query(res)}

    async def verify_and_run_optimized_sql(self, state: SqlImprovementState) -> SqlImprovementState:
        async def run_sql(sql):
            return await asyncio.to_thread(self.bq_client.execute_sql_query, sql)

        results = await asyncio.gather(*[run_sql(state["optimized_sql"])])
        return {"optimized_sql_res": self._evaluate_query(results[0])}
