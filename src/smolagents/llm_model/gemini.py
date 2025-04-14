from os import environ

from smolagents import LiteLLMModel


def get_model():
    """
    Initializes and returns a LiteLLMModel instance.

    This function retrieves the Google API key and model ID from environment variables,
    and then uses these values to create and return a LiteLLMModel object.
    The default model ID is 'gemini/gemini-2.0-flash' if not provided
    in the environment.

    Returns:
        LiteLLMModel: An instance of the LiteLLMModel class, configured with the
            specified API key and model ID.
    """
    GEMINI_API_KEY = environ.get("GOOGLE_API_KEY")
    model_id = environ.get("MODEL_ID", "gemini/gemini-2.0-flash")
    model = LiteLLMModel(model_id=model_id, api_key=GEMINI_API_KEY)
    return model
