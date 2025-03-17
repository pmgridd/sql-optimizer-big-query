import json
import logging
import os

from dotenv import load_dotenv
from google.cloud import aiplatform
from google.oauth2 import service_account
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


logging.basicConfig(
    format=f"%(asctime)s: %(levelname)s - %(message)s",
    level=logging.DEBUG, 
    datefmt="%m/%d/%Y %H:%M:%S",
)

logger = logging.getLogger(__name__)


def setup_airplatform() -> None:
    GCP_REGION = os.getenv("GCP_REGION", "us-central1")
    GCP_PROJECT = os.getenv("GCP_PROJECT", "gd-gcp-rnd-analytical-platform")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if json.loads(GOOGLE_APPLICATION_CREDENTIALS)["type"] == "authorized_user":
        with open("credentials.json", "w") as file:
            file.write(GOOGLE_APPLICATION_CREDENTIALS)  # dev env only
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"
        aiplatform.init(location=GCP_REGION, project=GCP_PROJECT)
    else:
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(GOOGLE_APPLICATION_CREDENTIALS)
        )
        aiplatform.init(location=GCP_REGION, project=GCP_PROJECT, credentials=credentials)

def create_llm(model_name="gemini-2.0-flash", temperature=1.0):
    """
    Creates a Langchain ChatGoogleGenerativeAI LLM.

    Args:
        model_name (str): The name of the Google Gemini model to use.
        temperature (float): The temperature setting for the model.

    Returns:
        ChatGoogleGenerativeAI: A Langchain ChatGoogleGenerativeAI LLM.
    """

    llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
    return llm