"""Define the configurable parameters for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.configuration import BaseConfiguration
from backend.retrieval_graph.propmts import prompts_langsmith
from backend.retrieval_graph.propmts import prompt_text


@dataclass(kw_only=True)
class AgentConfiguration(BaseConfiguration):
    """The configuration for the agent."""

    # models

    query_model: str = field(
        default="openai/gpt-4o-mini",
        metadata={
            "description": "The language model used for processing and refining queries. Should be in the form: provider/model-name."
        },
    )

    response_model: str = field(
        default="openai/gpt-4o-mini",
        metadata={
            "description": "The language model used for generating responses. Should be in the form: provider/model-name."
        },
    )

    # prompts
    plan_system_prompt: str = field(
        default=prompt_text.JOB_PLAN_GENERATION_SYSTEM_PROMPT,
        metadata={"description": "The system prompt used for generating responses."},
    )

    query_system_prompt: str = field(
        default=prompt_text.JOB_QUERY_GENERATION_SYSTEM_PROMPT,
        metadata={"description": "The system prompt used for generating responses."},
    )

    writing_system_prompt: str = field(
        default=prompt_text.JOB_WRITING_SYSTEM_PROMPT,
        metadata={"description": "The system prompt used for generating responses."},
    )

    router_system_prompt: str = field(
        default=prompts_langsmith.ROUTER_SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt used for classifying user questions to route them to the correct node."
        },
    )

    more_info_system_prompt: str = field(
        default=prompts_langsmith.MORE_INFO_SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt used for asking for more information from the user."
        },
    )

    general_system_prompt: str = field(
        default=prompts_langsmith.GENERAL_SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt used for responding to general questions."
        },
    )

    research_plan_system_prompt: str = field(
        default=prompts_langsmith.RESEARCH_PLAN_SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt used for generating a research plan based on the user's question."
        },
    )

    generate_queries_system_prompt: str = field(
        default=prompts_langsmith.GENERATE_QUERIES_SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt used by the researcher to generate queries based on a step in the research plan."
        },
    )

    response_system_prompt: str = field(
        default=prompts_langsmith.RESPONSE_SYSTEM_PROMPT,
        metadata={"description": "The system prompt used for generating responses."},
    )
