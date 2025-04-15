from typing_extensions import TypedDict
from typing import Optional
from dataclasses import dataclass


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


@dataclass
class SqlImprovementState(TypedDict):
    sql: str
    tables: list[SchemaInfo]
    antipatterns: list[dict]
    improvements: list[str]
    optimized_sql: str
    sql_res: dict
    optimized_sql_res: dict
    error: Optional[str]
    exectution_plan: list[str]
    attempt: int
