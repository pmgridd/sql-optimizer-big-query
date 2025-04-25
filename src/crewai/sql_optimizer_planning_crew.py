import os
import json

from src.crewai.models import (
    QueryStats,
    QueryInfo,
    QuerySuggestions,
    BestQueryChoice,
    ImprovementsAnalysis,
)
from src.crewai.bq_client import BigQueryClient
from src.common.env_setup import GCP_PROJECT, setup_aiplatform
from src.crewai.tools import sql_tools
from crewai import Agent, Crew, Task, Process, LLM
from crewai.project import CrewBase, agent, task, crew


@CrewBase
class SqlAnalysisPlanningCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/planning_tasks.yaml"
    llm = LLM(
        model="gemini/gemini-2.0-flash",
        temperature=0.1,
        vertex_credentials=json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")),
    )
    manager_llm = LLM(
        model="gemini/gemini-2.0-flash",
        temperature=0.1,
        vertex_credentials=json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")),
    )
    bq_client: BigQueryClient = BigQueryClient(
        project_id=GCP_PROJECT, credentials=setup_aiplatform()
    )

    @agent
    def sql_developer(self) -> Agent:
        return Agent(
            config=self.agents_config["sql_developer"],
            llm=self.llm,
            tools=[sql_tools.QueryTool(self.bq_client), sql_tools.MetadataTool(self.bq_client)],
            verbose=True,
        )

    @task
    def sql_query_execution(self) -> Task:
        return Task(
            config=self.tasks_config["sql_query_execution"],
            output_pydantic=QueryStats,
        )

    @task
    def sql_query_analysis(self) -> Task:
        return Task(config=self.tasks_config["sql_query_analysis"], output_pydantic=QueryInfo)

    @task
    def suggest_optimizations(self) -> Task:
        return Task(
            config=self.tasks_config["suggest_optimizations"],
            output_pydantic=QuerySuggestions,
        )

    @task
    def execute_improvement_variants(self) -> Task:
        return Task(
            config=self.tasks_config["execute_improvement_variants"],
            output_pydantic=ImprovementsAnalysis,
        )

    @task
    def suggest_best_query(self) -> Task:
        return Task(
            config=self.tasks_config["suggest_best_query"],
            context=[
                self.execute_improvement_variants(),
            ],
            output_pydantic=BestQueryChoice,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            planning=True,
            verbose=True,
            planning_llm=self.manager_llm,
        )
