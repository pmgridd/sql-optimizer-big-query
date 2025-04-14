from os import environ

import agentops
from openinference.instrumentation.smolagents import SmolagentsInstrumentor


def setup_agentops_telemetry():
    AGENTOPS_API_KEY = environ.get("AGENTOPS_API_KEY")
    agentops.init(api_key=AGENTOPS_API_KEY, default_tags=["smolagents"])
    SmolagentsInstrumentor().instrument()


setup_telemetry = setup_agentops_telemetry
