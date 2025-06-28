from dotenv import load_dotenv
from typing import Annotated

from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict
from langchain_community.tools import DuckDuckGoSearchRun

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, create_react_agent, tools_condition

import os

load_dotenv()

INFERENCE_SERVER_OPENAI = os.getenv("LLAMA_STACK_SERVER_OPENAI")
API_KEY=os.getenv("OPENAI_API_KEY", "not applicable")
INFERENCE_MODEL=os.getenv("INFERENCE_MODEL")

# For example:
#INFERENCE_SERVER_OPENAI = "http://localhost:8321/v1/openai/v1"
#INFERENCE_MODEL = "meta-llama/Llama-3.2-3B-Instruct"
#INFERENCE_SERVER_OPENAI = "https://api.openai.com/v1"
#INFERENCE_MODEL = "gpt-4o-mini"

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    #print("Invoking multiply: ", a, " x ",  b)
    return a * b

llm = init_chat_model(
    INFERENCE_MODEL,
    model_provider="openai",
    api_key=API_KEY,
    base_url=INFERENCE_SERVER_OPENAI,
    use_responses_api=True
)

print(llm.invoke("Hello"))

### Option 1: using prebuilt ReAct agent loop
print("Option 1: using prebuilt ReAct agent loop")
agent = create_react_agent(
    llm,
    [
        multiply,
        {"type": "web_search_preview_2025_03_11"}, # use web_search_preview when using OpenAI rather than Llama Stack
        {
            "type": "mcp",
            "server_label": "gitmcp",
            "server_url": "https://gitmcp.io/rh-ai-kickstart/RAG",
            "require_approval": "never",
        },
    ]
)

response = agent.invoke(
    {"messages": [{"role": "user", "content": "Who won Roland Garros for men in 2025?"}]}
)

for m in response['messages']:
    m.pretty_print()

response = agent.invoke(
    {"messages": [{"role": "user", "content": "How much is 11 times 11?"}]}
)

for m in response['messages']:
    m.pretty_print()

response = agent.invoke(
    {"messages": [{"role": "user", "content": "What are the components of the Red Hat RAG Kickstart?"}]}
)

for m in response['messages']:
    m.pretty_print()


### Building a graph with websearch and tool loops
print("Option 2: building a graph with tool loop")
llm_with_tools = llm.bind_tools(
    [
        multiply,
        {"type": "web_search_preview"},
        {
            "type": "mcp",
            "server_label": "gitmcp",
            "server_url": "https://gitmcp.io/rh-ai-kickstart/RAG",
            "require_approval": "never",
        },
    ])

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    #print(message)
    return {"messages": [message]}

graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode([multiply]))

graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph = graph_builder.compile()

response = graph.invoke(
    {"messages": [{"role": "user", "content": "Who won Roland Garros for men in 2025?"}]})

for m in response['messages']:
    m.pretty_print() 

response = graph.invoke(
    {"messages": [{"role": "user", "content": "How much is 11 times 11?"}]})

for m in response['messages']:
    m.pretty_print() 