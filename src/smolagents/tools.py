from smolagents import Tool

from ..common.constants import SQL_ANTIPATTERNS
from .bq_client import BigQueryClient


class TableMetadataTool(Tool):
    name = "table_metadata"
    description = "Allows you to get table metadata."
    inputs = {
        "table_id": {
            "type": "string",
            "description": "The ID of the table in the format 'dataset.table_name'.",
        }
    }
    output_type = "object"

    def __init__(self, bq_client: BigQueryClient):
        self.bq_client = bq_client
        super().__init__()

    def forward(self, table_id: str) -> dict:
        metadata = self.bq_client.get_table_metadata(table_id=table_id)
        return metadata


class AntipatternsTool(Tool):
    name = "antipaterns_info"
    description = "Allows you to get a dict of known SQL antipatterns descriptions."
    inputs = {}
    output_type = "object"

    def forward(self) -> dict:
        antipaterns_dict = SQL_ANTIPATTERNS
        return antipaterns_dict
