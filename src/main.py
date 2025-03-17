import os
import logging
from src.env_setup import *
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Query that is optimized web search.")
    justification: str = Field(
        None, justification="Why this query is relevant to the user's request."
    )

def multiply(a: int, b: int) -> int:
    return a * b


def main():
    logger.info("hello world")
    llm = create_llm()
    print(f"Created LLM: {llm}")
    
    structured_llm = llm.with_structured_output(SearchQuery)

    # Invoke the augmented LLM
    output = structured_llm.invoke("How does Calcium CT score relate to high cholesterol?")
    print(output.search_query)
    print(output.justification)

    # Augment the LLM with tools
    llm_with_tools = llm.bind_tools([multiply])

    # Invoke the LLM with input that triggers the tool call
    msg = llm_with_tools.invoke("What is 2 times 3?")

    # Get the tool call
    print(msg.tool_calls)

  

    return True

if __name__ == "__main__":
    main()
