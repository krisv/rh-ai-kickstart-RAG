from flask import Flask, request, jsonify, send_from_directory
from pydantic import BaseModel, Field
from typing_extensions import Literal
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv
import asyncio

load_dotenv()

INFERENCE_SERVER_OPENAI = os.getenv("LLAMA_STACK_SERVER_OPENAI")
API_KEY=os.getenv("OPENAI_API_KEY", "not applicable")
INFERENCE_MODEL=os.getenv("INFERENCE_MODEL")

# For example:
INFERENCE_SERVER_OPENAI = "http://localhost:8321/v1/openai/v1"
INFERENCE_MODEL = "gpt-4-turbo" #"llama3.2:3b-instruct-fp16"
#INFERENCE_SERVER_OPENAI = "https://api.openai.com/v1"
#INFERENCE_MODEL = "gpt-4o-mini"

llm = init_chat_model(
    INFERENCE_MODEL,
    model_provider="openai",
    api_key=API_KEY,
    base_url=INFERENCE_SERVER_OPENAI,
    use_responses_api=True
)

@tool
def sendEmail(subject: str, body: str):
    """Send an email from with the given subject and body.  Do not use attachments"""
    print(f"Sending email '{subject}' with body: {body}")
tools = [sendEmail]

class State(TypedDict):
    input: str
    messages: Annotated[list, add_messages]
    decision: str
    data: str

# Define topic_llm for use in topic_agent
web_search_tool = {"type": "web_search_preview"}
topic_tools = tools + [web_search_tool]
topic_llm = llm.bind_tools(topic_tools)

def topic_llm_node(state: State):
    message = topic_llm.invoke(state["messages"])
    return {"messages": [message]}

def init_topic_message(state: State):
    return {"messages": [{'role': 'user', 'content': 'First do a web search for the given topic and summarize the results, then send an email with the summary: ' + state['data']}]}

topic_agent_builder = StateGraph(State)
topic_agent_builder.add_node("set_message", init_topic_message)
# Use a lambda for the LLM invocation node
topic_agent_builder.add_node("llm_node", topic_llm_node)
topic_agent_builder.add_node("tools", ToolNode(tools))
topic_agent_builder.add_edge(START, "set_message")
topic_agent_builder.add_edge("set_message", "llm_node")
topic_agent_builder.add_edge("llm_node", "tools")
topic_agent_builder.add_conditional_edges("llm_node", tools_condition)
topic_agent = topic_agent_builder.compile()

def github_llm_node(state: State):
    repo_url = state['data'].replace('github.com', 'gitmcp.io')
    mcp_tool = {
        "type": "mcp",
        "server_label": "gitmcp",
        "server_url": repo_url,
        "require_approval": "never",
    }
    print(mcp_tool)
    github_tools = tools + [mcp_tool]
    github_llm = llm.bind_tools(github_tools)
    message = github_llm.invoke(state["messages"])
    return {"messages": [message]}

def init_github_message(state: State):
    return {"messages": [{'role': 'user', 'content': 'First retrieve the README.md and send an email with the summary.'}]}

github_agent_builder = StateGraph(State)
github_agent_builder.add_node("set_message", init_github_message)
github_agent_builder.add_node("llm_node", github_llm_node)
github_agent_builder.add_node("tools", ToolNode(tools))
github_agent_builder.add_edge(START, "set_message")
github_agent_builder.add_edge("set_message", "llm_node")
# github_agent_builder.add_edge("tools", "llm_node")
github_agent_builder.add_conditional_edges("llm_node", tools_condition)
github_agent = github_agent_builder.compile()

class TriageSchema(BaseModel):
    """Analyze the unread email and route it according to its content."""

    classification: Literal["topic", "github", "unknown"] = Field(
        description="The classification of the input: 'topic' if the input is a topic to research, "
        "'github' if the input is a GitHub repository to research, "
        "'unknown' for everything else",
    )

def triage_agent(state: State):
    # Determine if the message is a topic or a GitHub reference
    triage_llm = llm.with_structured_output(TriageSchema)
    triage_result = triage_llm.invoke([{'role': 'user', 'content': 'Determine if the following message is a topic or a GitHub reference: ' + state['input']}])
    print(f"Triage result: {triage_result}")
    if 'topic' == triage_result.classification:
        state['decision'] = 'topic'
        state['data'] = state['input']
    elif 'github' == triage_result.classification:
        state['decision'] = 'github'
        state['data'] = state['input']
    else:
        state['decision'] = 'unknown'
        state['data'] = ''
        return {'messages': [{'role': 'assistant', 'content': "Unable to determine request type."}]}
    return state

def route_to_next_node(state: State) -> Literal['topic_agent', 'github_agent', '__end__']:
    if state['decision'] == 'topic':
        return 'topic_agent'
    elif state['decision'] == 'github':
        return 'github_agent'
    else:
        return '__end__'

overall_workflow = StateGraph(State)
overall_workflow.add_node("triage_agent", triage_agent)
overall_workflow.add_node("topic_agent", topic_agent)
overall_workflow.add_node("github_agent", github_agent)
overall_workflow.add_edge(START, "triage_agent")
overall_workflow.add_conditional_edges("triage_agent", route_to_next_node)
workflow = overall_workflow.compile()

async def invoke_workflow_async(idea):
    response = await asyncio.to_thread(workflow.invoke, {"input": idea})
    return response

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/submit-idea', methods=['POST'])
def submit_idea():
    idea = request.form.get('idea')
    if not idea:
        return jsonify({'error': 'No idea provided'}), 400

    # Process the idea using your workflow asynchronously
    asyncio.create_task(invoke_workflow_async(idea))
    return jsonify({'status': 'Processing started'})

if __name__ == '__main__':
    app.run(debug=True) 