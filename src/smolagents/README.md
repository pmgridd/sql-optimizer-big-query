## Environment Variables Setup

To properly run this application, you need to set up the following environment variables. You can set these in your shell environment or in a `.env` file in the root of the repository.

### Google Cloud Platform

| Variable | Description | Example Value |
| ---- | ----| ---- |
| `GOOGLE_APPLICATION_CREDENTIALS`| Path to the JSON file containing your Google Cloud service account credentials.  **Required for BigQuery access.** | `/path/to/your/service-account.json` |
| `GCP_PROJECT` | Your Google Cloud Project ID. Used for BigQuery. | `YOUR-GCP_PROJECT` |
| `MODEL_ID` | The default LLM model ID. | `gemini/gemini-2.0-flash` |
| `GEMINI_API_KEY` | API key for accessing Google services. Google AI Studio API key. | `AI...` |

### OpenAI API

| Variable | Description | Example Value |
| ---- | ---- | ---- |
| `OPENAI_API_KEY` | API key for accessing OpenAI services. | `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `MODEL_ID` | The default LLM model ID. | `gpt-4o` |

### Arize Phoenix

| Variable | Description | Example Value |
| ---- | ---- | ---- |
| `OTEL_ENDPINT` | Endpoint for OpenTelemetry (OTEL) data, used by Arize Phoenix. | `http://localhost:4317` |
| `OTEL_PROJECT_NAME` | Project name for OpenTelemetry, used to organize data in Arize Phoenix. | `your-project-id` |

### Langfuse

| Variable | Description | Example Value |
| ---- | ---- | ---- |
| `LANGFUSE_SECRET_KEY` | Secret key for accessing Langfuse Cloud. Keep this secure. | `sk_xxxxxxxxxxxxxxxxxxxxxxxx` |
| `LANGFUSE_PUBLIC_KEY` | Public key for identifying your application to Langfuse. | `pk_xxxxxxxxxxxxxxxxxxxxxxxx` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Endpoint for sending OpenTelemetry data to Langfuse Cloud. | `https://cloud.langfuse.com/api/public/otel`, `http://localhost:3000/api/public/otel` |

### AgentOps

| Variable | Description | Example Value |
| ---- | ---- | ---- |
| `AGENTOPS_API_KEY` | API key for accessing the AgentOps platform. | `YOUR_AGENTOPS_API_KEY` |

### EvidentlyAI

| Variable | Description | Example Value |
| ---- | ---- | ---- |
| `EVIDENTLY_API_KEY`   | API key for accessing the EvidentlyAI platform. | `YOUR_EVIDENTLY_API_KEY` |
| `EVIDENTLY_PROJECT_ID` | Project ID for EvidentlyAI. | `your-project-id` |

### LangSmith

| Variable | Description | Example Value |
| ---- | ---- | ---- |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Endpoint for OpenTelemetry. | `https://api.smith.langchain.com/otel` |
| `LANGSMITH_API_KEY`         | API key for accessing the LangSmith platform. | `ls_xxxxxxxxxxxxxxxxxxxxxxxx` |
| `LANGSMITH_PROJECT`         | LangSmith Project. | `your-project-id` |

### W&B Weave

| Variable | Description | Example Value |
| ---- | ---- | ---- |
| `WANDB_API_KEY` | API key for accessing Weights & Biases (W&B). | `YOUR_WANDB_API_KEY` |
