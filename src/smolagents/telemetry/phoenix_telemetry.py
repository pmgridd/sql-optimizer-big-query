from os import environ

from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from phoenix.otel import register


def setup_phoenix_telemetry():
    otel_endpoint = environ.get("OTEL_ENDPINT", "http://localhost:4317")
    otel_project_name = environ.get("OTEL_PROJECT_NAME", "smolagents")
    register(endpoint=otel_endpoint, project_name=otel_project_name, batch=True)
    SmolagentsInstrumentor().instrument()


setup_telemetry = setup_phoenix_telemetry
