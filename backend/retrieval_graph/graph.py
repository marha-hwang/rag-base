"""Main entrypoint for the conversational retrieval graph.

This module defines the core structure and functionality of the conversational
retrieval graph. It includes the main graph definition, state management,
and key functions for processing & routing user queries, generating research plans to answer user questions,
conducting research, and formulating responses.
"""

from typing import Any, Literal, TypedDict, cast

from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from backend.retrieval_graph.configuration import AgentConfiguration
from backend.retrieval_graph.researcher_graph.graph import graph as researcher_graph
from backend.retrieval_graph.state import AgentState, InputState
from backend.utils import format_docs, load_chat_model


async def create_research_plan(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, list[str]]:
    """Create a step-by-step research plan for answering a LangChain-related query.

    Args:
        state (AgentState): The current state of the agent, including conversation history.
        config (RunnableConfig): Configuration with the model used to generate the plan.

    Returns:
        dict[str, list[str]]: A dictionary with a 'steps' key containing the list of research steps.
    """

    class Plan(TypedDict):
        """Generate research plan."""
        steps: list[str]

    configuration = AgentConfiguration.from_runnable_config(config)
    structured_output_kwargs = (
        {"method": "function_calling"} if "openai" in configuration.query_model else {}
    )

    # 내부에서 |(파이프) LCEL문법을 사용하여 Plan 타입으로 출력하도록 함
    # with_structured_output : return llm | output_parser
    # 어떻게 동작하지? 프롬프트에서 출력 형식을 지정하는 것인가?
    model = load_chat_model(configuration.query_model).with_structured_output(
        Plan, **structured_output_kwargs
    )

    # 프롬프트 메시지 생성
    messages = [
        {"role": "system", "content": configuration.plan_system_prompt}
    ] + state.messages

    # invoke, ainvoke의 차이 : ainvoke는 비동기 함수, invoke는 동기 함수
    response = cast(
        Plan, await model.ainvoke(messages, {"tags": ["langsmith:nostream"]})
    )

    # agent state 업데이트
    return {
        "steps": response["steps"],
        "documents": "delete",
        "query": state.messages[-1].content,
    }


async def conduct_research(state: AgentState) -> dict[str, Any]:
    """Execute the first step of the research plan.

    This function takes the first step from the research plan and uses it to conduct research.

    Args:
        state (AgentState): The current state of the agent, including the research plan steps.

    Returns:
        dict[str, list[str]]: A dictionary with 'documents' containing the research results and
                              'steps' containing the remaining research steps.

    Behavior:
        - Invokes the researcher_graph with the first step of the research plan.
        - Updates the state with the retrieved documents and removes the completed step.
    """

    # crate_research_plan에서 생성된 연구 계획의 첫 번째 단계를 사용하여 연구를 수행
    # researcher_graph를 호출하여 각 단계에 대한 문서를 검색
    # steps 목록에서 완료된 단계를 제거
    result = await researcher_graph.ainvoke({"question": state.steps[0]})
    return {"documents": result["documents"], "steps": state.steps[1:]}


def check_finished(state: AgentState) -> Literal["respond", "conduct_research"]:
    """Determine if the research process is complete or if more research is needed.

    This function checks if there are any remaining steps in the research plan:
        - If there are, route back to the `conduct_research` node
        - Otherwise, route to the `respond` node

    Args:
        state (AgentState): The current state of the agent, including the remaining research steps.

    Returns:
        Literal["respond", "conduct_research"]: The next step to take based on whether research is complete.
    """

    # 연구 계획에 남은 단계가 있는지 확인
    if len(state.steps or []) > 0:
        return "conduct_research"
    else:
        return "respond"


async def respond(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, list[BaseMessage]]:
    """Generate a final response to the user's query based on the conducted research.

    This function formulates a comprehensive answer using the conversation history and the documents retrieved by the researcher.

    Args:
        state (AgentState): The current state of the agent, including retrieved documents and conversation history.
        config (RunnableConfig): Configuration with the model used to respond.

    Returns:
        dict[str, list[str]]: A dictionary with a 'messages' key containing the generated response.
    """
    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.response_model)
    # TODO: add a re-ranker here
    top_k = 20
    
    # 검색한 자료들을 문자열로 포맷팅 하여 컨텍스트로 사용
    context = format_docs(state.documents[:top_k])
    response = await model.ainvoke(
        [
            {
                "role": "system",
                "content": configuration.writing_system_prompt.format(context=context),
            },
            *state.messages,
        ]
    )
    return {"messages": [response], "answer": response.content}


# 전체 그래프 정의
"""
Input --START--> create_research_plan -> conduct_research -> respond --END--> Output
                                                |     ^
                                                |     |
                                                ㄴㅡㅡcheck_finished                                           
"""

# researcher_graph 정의(conduct_research 노드에서 사용)
"""
Input --START--> generate_queries -> retrieve_documents --END--> Output
                            |     -> retrieve_documents
             retrieve_in_parallel -> retrieve_documents
                            ㄴㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ|                                           
"""

# BaseConfiguration을 상속받는 AgentConfiguration을 사용
# Baseconfiguration은 from_runnable_config 메서드를 통해 RunnableConfig 객체에서 구성 인스턴스를 생성하는 기능을 제공
# RunnableConfig 객체는 그래프 실행에 필요한 다양한 매개변수(예: 모델 선택, 검색 매개변수 등)를 포함
# InputState는 어떻게 동작하지?
builder = StateGraph(AgentState, input=InputState, config_schema=AgentConfiguration)
builder.add_node(create_research_plan)
builder.add_node(conduct_research)
builder.add_node(respond)

builder.add_edge(START, "create_research_plan")
builder.add_edge("create_research_plan", "conduct_research")

#  check_finished : return "conduct_research" or "respond"
builder.add_conditional_edges("conduct_research", check_finished)
builder.add_edge("respond", END)

# Compile into a graph object that you can invoke and deploy.
#Compiles the state graph into a CompiledStateGraph object.
graph = builder.compile()
graph.name = "RetrievalGraph"
