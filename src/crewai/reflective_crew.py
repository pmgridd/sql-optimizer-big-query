import os
import json

from src.crewai.models import (
    QueryStats,
    EvaluationSnapshot,
    ReflectionDecision,
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
class ReflectiveLoopCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/reflective_loop.yaml"
    # llm = LLM(
    #     model="openai/gpt-4o",
    #     temperature=0.1,
    # )
    llm = LLM(
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
    def execute_initial_query(self) -> Task:
        return Task(
            config=self.tasks_config["execute_initial_query"], output_pydantic=EvaluationSnapshot
        )

    @task
    def generate_improvements_round(self) -> Task:
        return Task(
            config=self.tasks_config["generate_improvements_round"],
            output_pydantic=QuerySuggestions,
        )

    @task
    def benchmark_improvements_round(self) -> Task:
        return Task(
            config=self.tasks_config["benchmark_improvements_round"],
            output_pydantic=ImprovementsAnalysis,
        )

    @task
    def reflect_and_synthesize_round(self) -> Task:
        return Task(
            config=self.tasks_config["reflect_and_synthesize_round"],
            context=[
                self.generate_improvements_round(),
                self.benchmark_improvements_round(),
            ],
            output_pydantic=QuerySuggestions,
        )

    @task
    def finalize_best_query(self) -> Task:
        return Task(
            config=self.tasks_config["finalize_best_query"],
            context=[
                self.reflect_and_synthesize_round(),
            ],
            output_pydantic=BestQueryChoice,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
