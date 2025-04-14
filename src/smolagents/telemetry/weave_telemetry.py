import base64
from os import environ

from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_weave_telemetry():
    WANDB_BASE_URL = "https://trace.wandb.ai"
    PROJECT_ID = "kopagm-grid-dynamics/smolagents"
    OTEL_EXPORTER_OTLP_ENDPOINT = f"{WANDB_BASE_URL}/otel/v1/traces"
    WANDB_API_KEY = environ.get("WANDB_API_KEY")
    AUTH = base64.b64encode(f"api:{WANDB_API_KEY}".encode()).decode()
    OTEL_EXPORTER_OTLP_HEADERS = {
        "Authorization": f"Basic {AUTH}",
        "project_id": PROJECT_ID,
    }
    tracer_provider = TracerProvider()
    exporter = OTLPSpanExporter(
        endpoint=OTEL_EXPORTER_OTLP_ENDPOINT,
        headers=OTEL_EXPORTER_OTLP_HEADERS,
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    SmolagentsInstrumentor().instrument(tracer_provider=tracer_provider)


setup_telemetry = setup_weave_telemetry
