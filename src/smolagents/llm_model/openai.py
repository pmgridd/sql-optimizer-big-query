from os import environ

from smolagents import OpenAIServerModel


def get_model():
    """
    Initializes and returns an OpenAIServerModel instance.

    This function retrieves the OpenAI API key and model ID from the environment variables
    and uses them to create and return an OpenAIServerModel object.
    The default model ID is 'gpt-4o' if not provided in the environment.

    Returns:
        OpenAIServerModel: An instance of the OpenAIServerModel class, configured with the
            OpenAI API key and model ID.
    """
    OPENAI_API_KEY = environ.get("OPENAI_API_KEY")
    MODEL_ID = environ.get("MODEL_ID", "gpt-4o")
    model = OpenAIServerModel(model_id=MODEL_ID, api_key=OPENAI_API_KEY)
    return model
