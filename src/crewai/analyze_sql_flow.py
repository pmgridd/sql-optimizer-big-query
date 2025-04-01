from crewai.flow.flow import Flow, listen, start
from src.common.env_setup import setup_aiplatform, GCP_PROJECT
from src.common.bq_client import BigQueryClient
from src.common.utils import (
    get_table_schema_prompt,
    get_antipatterns_prompt,
    get_suggestions_prompt,
    get_optimized_sql_prompt,
    evaluate_query,
)
from crewai import LLM
from src.common.sql_analyzer import SqlImprovementState
import logging
import os
import json

logger = logging.getLogger(__name__)


class SqlAnalysisFlow(Flow[SqlImprovementState]):
    llm = LLM(
        model="gemini/gemini-2.0-flash",
        temperature=1.0,
        vertex_credentials=json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")),
    )
    bq_client = BigQueryClient(project_id=GCP_PROJECT, credentials=setup_aiplatform())

    @start()
    def verify_sql(self):
        """Flow entrypoint."""
        logger.info(f"Starting analysis flow for SQL query: {self.state['sql']}")
        # if random.random() < 0.6:  # 60% chance of failure
        #     raise Exception("Simulated BigQuery query failure")
        self.state["sql_res"] = self.bq_client.execute_sql_query(self.state["sql"])
        logger.info(f"Results of initial SQL query: {self.state['sql_res']}")

    @listen(verify_sql)
    def identify_tables(self):
        """First step"""
        logger.info(f"Identify tables state {self.state}")
        msg = self.llm.call(get_table_schema_prompt(self.state["sql"]))
        logger.info(f"LLM response {msg}")
        if "no_tables_found" not in msg.strip():
            tables = [self.bq_client.get_table_metadata(table.strip()) for table in msg.split(",")]
            logger.info(f"Identified tables referenced in the query: {tables}")
            self.state["tables"] = tables
        else:
            raise RuntimeError("No tables found in the provided SQL query.")

    @listen(identify_tables)
    def antipatterns(self):
        msg = self.llm.call(get_antipatterns_prompt(self.state["sql"]))
        antipatterns = []
        current_pattern = {}
        for line in msg.split("\n"):
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
        self.state["antipatterns"] = antipatterns
        logger.info(f"Identified antipatterns: {antipatterns}")

    # @listen(antipatterns)
    # def previous_optimizations():
    #     pass

    @listen(antipatterns)
    def suggestions(self):
        """Get optimization suggestions using a focused prompt."""
        try:
            msg = self.llm.call(
                get_suggestions_prompt(
                    self.state["sql"], self.state["antipatterns"], self.state["tables"]
                )
            )
            suggestions = []
            for line in msg.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    suggestions.append(line[2:])
            logger.info(f"Suggested improvements: {suggestions}")
            return {"improvements": suggestions}

        except Exception as e:
            print(f"Error getting suggestions: {str(e)}")
            return {"improvements": []}

    @listen(suggestions)
    def optimize(self):
        """Get optimization suggestions using a focused prompt."""
        try:
            msg = self.llm.call(
                get_optimized_sql_prompt(
                    self.state["sql"], self.state["antipatterns"], self.state["tables"]
                )
            )

            def clean_sql_string(sql_string):
                return sql_string.replace("```sql", "").replace("```", "").strip()

            return {"optimized_sql": clean_sql_string(msg)}

        except Exception as e:
            print(f"Error getting suggestions: {str(e)}")
            return {"optimized_sql": ""}

    @listen(optimize)
    def verify_optimized_sql(self):
        results = self.bq_client.execute_sql_query(self.state["optimized_sql"])
        return {"optimized_sql_res": evaluate_query(results[0])}
