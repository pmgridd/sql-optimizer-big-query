from typing_extensions import TypedDict
from typing import Optional
from pydantic import BaseModel
from dataclasses import dataclass


class ColumnInfo(BaseModel):
    column_name: str
    column_type: str


class SchemaInfo(BaseModel):
    """Contains table schema and statistics information."""

    table_name: str
    dataset_name: str
    gcp_project_name: str
    columns: list[ColumnInfo]
    row_count: Optional[int] = None
    size_bytes: Optional[int] = None


class QueryInfo(BaseModel):
    """
    Contains the original SQL plus multiple SchemaInfo for all
    tables referenced in the query.
    """

    sql: str
    tables: list[SchemaInfo]


class QueryStats(BaseModel):
    """Contains table schema and statistics information for a BigQuery job."""

    total_bytes_processed: int
    total_bytes_billed: int
    billing_tier: int
    execution_time_seconds: float
    cache_hit: bool
    num_dml_affected_rows: int
    sql: str


class Antipattern(BaseModel):
    """Represents a single identified SQL antipattern."""

    code: str
    name: str
    description: str
    impact: str
    location: str
    suggestion: str


class QueryAnalysis(BaseModel):
    """
    Contains the original SQL plus multiple Antipattern objects for all
    antipatterns identified in the query.
    """

    sql: str
    antipatterns: list[Antipattern]


class ProposedImprovement(BaseModel):
    """A single proposed improvement to the original query."""

    improved_sql: str
    rationale: str


class QuerySuggestions(BaseModel):
    """
    Contains the original SQL plus multiple ProposedImprovements.
    Each improvement is a candidate new query plus rationale.
    """

    original_sql: str
    improvements: list[ProposedImprovement]


class EvaluationSnapshot(BaseModel):
    """All artefacts from one round."""

    query_stats: QueryStats
    query_info: QueryInfo


class ReflectionDecision(BaseModel):
    """Reflection result that drives the loop."""

    continue_iterating: bool
    best_stats: QueryStats
    best_sql: str
    insights: str


class ImprovementsAnalysis(BaseModel):
    """
    Holds a list of proposed improved query candidates and execution stats for each.
    """

    improvements: list[ProposedImprovement]
    execution_stats: list[QueryStats]


class BestQueryChoice(BaseModel):
    """
    Holds the final chosen SQL from among original or improved variants,
    plus a short explanation/justification for that choice.
    """

    chosen_sql: str
    justification: str


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
