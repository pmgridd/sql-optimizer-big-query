from os import environ

from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from tracely import init_tracing


def setup_evidently_telemetry():
    EVIDENTLY_API_KEY = environ.get("EVIDENTLY_API_KEY")
    EVIDENTLY_PROJECT_ID = environ.get("EVIDENTLY_PROJECT_ID")
    trace_provider = init_tracing(
        address="https://app.evidently.cloud/",
        api_key=EVIDENTLY_API_KEY,
        project_id=EVIDENTLY_PROJECT_ID,
        export_name="smolagents",
    )
    SmolagentsInstrumentor().instrument(tracer_provider=trace_provider)


setup_telemetry = setup_evidently_telemetry
