import os
import logging
import google.cloud.logging
from dotenv import load_dotenv

from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.langchain_tool import LangchainTool

from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

import google.auth
import google.auth.transport.requests
import google.oauth2.id_token

# --- Setup Logging and Environment ---

cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

load_dotenv()

model_name = os.getenv("MODEL")

# Tool: Save prompt
def add_prompt_to_state(tool_context: ToolContext, prompt: str) -> dict[str, str]:
    tool_context.state["PROMPT"] = prompt
    logging.info(f"[State updated] Added to PROMPT: {prompt}")
    return {"status": "success"}

# Wikipedia tool
wikipedia_tool = LangchainTool(
    tool=WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
)

# Research agent
comprehensive_researcher = Agent(
    name="comprehensive_researcher",
    model=model_name,
    description="Research agent using Wikipedia",
    instruction="""
    You are a helpful research assistant. Answer the user's PROMPT using Wikipedia.

    PROMPT:
    { PROMPT }
    """,
    tools=[wikipedia_tool],
    output_key="research_data"
)

# Formatter agent
response_formatter = Agent(
    name="response_formatter",
    model=model_name,
    description="Formats response",
    instruction="""
    Convert RESEARCH_DATA into a friendly answer.

    RESEARCH_DATA:
    { research_data }
    """
)

# Workflow
tour_guide_workflow = SequentialAgent(
    name="tour_guide_workflow",
    sub_agents=[
        comprehensive_researcher,
        response_formatter,
    ]
)

# Root agent
root_agent = Agent(
    name="greeter",
    model=model_name,
    description="Main entry point",
    instruction="""
    Ask user what they want to know about animals.
    Save prompt using tool, then pass to workflow.
    """,
    tools=[add_prompt_to_state],
    sub_agents=[tour_guide_workflow]
)