from os import environ

from dotenv import load_dotenv

from .agent import MultiAgent
from .bq_client import BigQueryClient
from .demo_app import build_demo
from .input_samples import input_samples
from .llm_model.gemini import get_model
from .telemetry.langfuse_telemetry import setup_telemetry
from .tools import AntipatternsTool, TableMetadataTool

load_dotenv(override=True)


def main():
    model = get_model()
    setup_telemetry()
    GCP_PROJECT = environ.get("GCP_PROJECT")
    bq_client = BigQueryClient(project_id=GCP_PROJECT)
    tools = [TableMetadataTool(bq_client=bq_client), AntipatternsTool()]
    agent = MultiAgent(model=model, tools=tools)
    demo = build_demo(
        fn=agent.run,
        examples=input_samples,
    )
    demo.launch()


if __name__ == "__main__":
    main()
