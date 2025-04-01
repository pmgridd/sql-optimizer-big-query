from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, task, crew


@CrewBase
class SqlAnalysisCrew:
    """SQL Analysis agent"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def sql_developer(self) -> Agent:
        return Agent(config=self.agents_config["sql_developer"], verbose=True)

    @task
    def task_one(self) -> Task:
        return Task(config=self.tasks_config["task_one"])

    @task
    def task_two(self) -> Task:
        return Task(config=self.tasks_config["task_two"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            verbose=True,
        )
