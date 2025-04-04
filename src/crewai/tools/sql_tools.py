from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from src.common.bq_client import BigQueryClient
from src.common.models import QueryStats, SchemaInfo
from src.common.env_setup import GCP_PROJECT
from typing import Type
from pydantic import PrivateAttr


class QueryInput(BaseModel):
    """Input schema for a SQL query execution via BigQuery client."""

    sql: str = Field(description="String containing valid BigQuery SQL query.")


class TableMetadataInput(BaseModel):
    """Input schema for a table metadata retriever tool."""

    table: str = Field(description="String containing a BigQuery table identifier.")
    dataset: str = Field(description="String containing a BigQuery dataset identifier.")


class QueryTool(BaseTool):
    name: str = "SQL Query executor"
    description: str = (
        "This tool executes a given sql query using a pre-initialized and authenticated"
        " BigQuery client, waits for the query job to finish and returns the query job stats."
    )
    args_schema: Type[BaseModel] = QueryInput
    _bq_client: BigQueryClient = PrivateAttr()

    def __init__(self, bq_client: BigQueryClient, **kwargs):
        super().__init__(**kwargs)
        self._bq_client = bq_client

    def _run(self, sql: str) -> QueryStats:
        return self._bq_client.get_sql_query_stats(sql)


class MetadataTool(BaseTool):
    name: str = "BigQuery table metadata retriever"
    description: str = (
        "This tool fetches metadata (schema and size) for a given dataset and table name"
        " if it exists in the project using a pre-initialized and authenticated"
        " BigQuery client."
    )
    args_schema: Type[BaseModel] = TableMetadataInput
    _bq_client: BigQueryClient = PrivateAttr()

    def __init__(self, bq_client: BigQueryClient, **kwargs):
        super().__init__(**kwargs)
        self._bq_client = bq_client

    def _run(self, dataset, table: str) -> SchemaInfo:
        return self._bq_client.get_table_metadata(GCP_PROJECT, dataset, table)
