from os import environ

from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_langsmith_telemetry():
    LANGSMITH_ENDPOINT = "https://api.smith.langchain.com/otel/v1/traces"
    LANGSMITH_API_KEY = environ.get("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT = "smolagents"
    trace_provider = TracerProvider()
    otlp_exporter = OTLPSpanExporter(
        endpoint=LANGSMITH_ENDPOINT,
        headers={"x-api-key": LANGSMITH_API_KEY, "Langsmith-Project": LANGSMITH_PROJECT},
    )
    processor = BatchSpanProcessor(otlp_exporter)
    trace_provider.add_span_processor(processor)
    SmolagentsInstrumentor().instrument(tracer_provider=trace_provider)


setup_telemetry = setup_langsmith_telemetry
