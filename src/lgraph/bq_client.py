from google.cloud import bigquery
import time
from src.lgraph.models import ColumnInfo, SchemaInfo
import logging
from langchain.tools import Tool

logger = logging.getLogger(__name__)


class BigQueryClient:
    def __init__(self, project_id: str, credentials=None):
        """
        Initialize the BigQuery client.
        Args:
            project_id: Google Cloud project ID.
        """
        self.client = bigquery.Client(project=project_id, credentials=credentials)

    async def execute_sql_query(self, sql: str) -> dict:
        job_config = bigquery.QueryJobConfig()
        job_config.use_query_cache = False
        start_time = time.time()

        query_job = self.client.query(sql, job_config=job_config)
        query_job.result()  # Ensures the query completes before proceeding

        end_time = time.time()
        job = self.client.get_job(query_job.job_id)

        # Extract job metadata safely
        metadata = {
            "total_bytes_processed": job.estimated_bytes_processed
            if job.estimated_bytes_processed is not None
            else 0,
            "total_bytes_billed": job.total_bytes_billed
            if job.total_bytes_billed is not None
            else 0,
            "billing_tier": job.billing_tier if job.billing_tier is not None else 0,
            "execution_time_seconds": end_time - start_time,
            "cache_hit": getattr(job, "cache_hit", False),
            "num_dml_affected_rows": job.num_dml_affected_rows
            if job.num_dml_affected_rows is not None
            else 0,
            "sql": sql,
        }
        return metadata

    async def get_table_metadata(self, table_id: str) -> SchemaInfo:
        """
        Get metadata about a BigQuery table, formatted as a SchemaInfo object.

        Args:
            table_id: The ID of the table in the format "dataset.table_name".

        Returns:
            A SchemaInfo object containing the table schema and storage information.
        """
        table = self.client.get_table(table_id)  # Make an API request.

        columns = []
        for field in table.schema:
            column_info = ColumnInfo(
                column_name=field.name,
                column_type=field.field_type,
            )
            columns.append(column_info)

        schema_info = SchemaInfo(
            table_name=table_id,
            columns=columns,
            row_count=table.num_rows,
            size_bytes=table.num_bytes,
        )

        return schema_info

    def evaluate_query(self, results: dict) -> dict:
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
