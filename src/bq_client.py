from google.cloud import bigquery
import time

from google.cloud import bigquery
import time


class BigQueryClient:
    def __init__(self, project_id: str):
        """
        Initialize the BigQuery client.
        Args:
            project_id: Google Cloud project ID.
        """
        self.client = bigquery.Client(project=project_id)

    def execute_sql_query(self, sql: str) -> dict:
        """
        Execute an SQL query and return query statistics.

        Args:
            sql: The SQL query string.

        Returns:
            Dictionary containing query statistics, costs, and execution time.
        """
        job_config = bigquery.QueryJobConfig()
        start_time = time.time()
        query_job = self.client.query(sql, job_config=job_config)
        query_job.result()
        end_time = time.time()

        stats = query_job.statistics

        # Handle potential None values gracefully
        total_bytes_processed = stats.total_bytes_processed if stats.total_bytes_processed else 0
        total_bytes_billed = stats.total_bytes_billed if stats.total_bytes_billed else 0
        billing_tier = stats.billing_tier if stats.billing_tier else "N/A"
        cache_hit = stats.cache_hit if stats.cache_hit else False
        num_dml_affected_rows = query_job.num_dml_affected_rows if query_job.num_dml_affected_rows else 0

        metadata = {
            "total_bytes_processed": total_bytes_processed,
            "total_bytes_billed": total_bytes_billed,
            "billing_tier": billing_tier,
            "execution_time_seconds": end_time - start_time,
            "cache_hit": cache_hit,
            "num_dml_affected_rows": num_dml_affected_rows,
            "query": sql, #Include the query in the metadata for easier debugging
        }

        return metadata