from dataclasses import dataclass
from typing import Optional

from typing_extensions import TypedDict


@dataclass
class ColumnInfo(TypedDict):
    column_name: str
    column_type: str


@dataclass
class SchemaInfo(TypedDict):
    """Contains table schema and statistics information."""

    table_name: str
    columns: list[ColumnInfo]
    row_count: Optional[int] = None
    size_bytes: Optional[int] = None
