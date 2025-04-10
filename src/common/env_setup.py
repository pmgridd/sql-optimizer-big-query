import json
import logging
import os

from dotenv import load_dotenv
from google.cloud import aiplatform
from google.oauth2 import service_account
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import Langfuse
from langfuse.callback import CallbackHandler

load_dotenv()

GCP_REGION = os.getenv("GCP_REGION", "us-central1")
GCP_PROJECT = os.getenv("GCP_PROJECT", "gd-gcp-rnd-analytical-platform")
GCP_MODE = os.getenv("GCP_MODE", "LOCAL")

logging.basicConfig(
    format=f"%(asctime)s: %(levelname)s - %(message)s",
    level=logging.DEBUG,
    datefmt="%m/%d/%Y %H:%M:%S",
)

logger = logging.getLogger(__name__)


def setup_langfuse() -> Langfuse:
    langfuse = Langfuse(
        secret_key=os.getenv("LANGFUSE_PRIVATE_KEY", "[NOT_FILLED]"),
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "[NOT_FILLED]"),
        host=os.getenv("LANGFUSE_HOST", "[NOT_FILLED]"),
    )
    return langfuse


def setup_langfuse_callback() -> CallbackHandler:
    # langfuse = setup_langfuse()
    langfuse_handler = CallbackHandler(
        os.getenv("LANGFUSE_PUBLIC_KEY", "[NOT_FILLED]"),
        os.getenv("LANGFUSE_PRIVATE_KEY", "[NOT_FILLED]"),
        os.getenv("LANGFUSE_HOST", "[NOT_FILLED]"),
        environment="default",
    )
    return langfuse_handler


def setup_aiplatform():
    if GCP_MODE == "WIF":
        aiplatform.init(location=GCP_REGION, project=GCP_PROJECT)
    else:
        GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if json.loads(GOOGLE_APPLICATION_CREDENTIALS)["type"] == "authorized_user":
            with open("credentials.json", "w") as file:
                file.write(GOOGLE_APPLICATION_CREDENTIALS)  # dev env only
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"
            aiplatform.init(location=GCP_REGION, project=GCP_PROJECT)
            return None
        else:
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(GOOGLE_APPLICATION_CREDENTIALS)
            )
            aiplatform.init(location=GCP_REGION, project=GCP_PROJECT, credentials=credentials)
            return credentials


def create_llm(model_name="gemini-2.0-flash", temperature=1.0, callbacks=None):
    """
    Creates a Langchain ChatGoogleGenerativeAI LLM.

    Args:
        model_name (str): The name of the Google Gemini model to use.
        temperature (float): The temperature setting for the model.

    Returns:
        ChatGoogleGenerativeAI: A Langchain ChatGoogleGenerativeAI LLM.
    """

    llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature, callbacks=callbacks)
    return llm
