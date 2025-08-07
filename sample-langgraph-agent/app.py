import logging
from flask import Flask, request, jsonify, send_from_directory
from typing_extensions import Literal
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from datetime import datetime, date

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv(dotenv_path='config.env')
load_dotenv(dotenv_path='secret.env')

INFERENCE_SERVER_OPENAI = os.getenv("LLAMA_STACK_SERVER_OPENAI", "http://localhost:8321/v1/openai/v1")
API_KEY=os.getenv("OPENAI_API_KEY", "not applicable")
INFERENCE_MODEL=os.getenv("INFERENCE_MODEL", "ollama/llama3.2:3b-instruct-fp16")

logger.info(f"Connecting to {INFERENCE_SERVER_OPENAI} model {INFERENCE_MODEL}")

llm = init_chat_model(
    INFERENCE_MODEL,
    model_provider="openai",
    api_key=API_KEY,
    base_url=INFERENCE_SERVER_OPENAI,
    use_responses_api=True
)

## Tool section, defining local tools and built-in tools

# 1. Local Tools
# Define local tools, these are just python methods that the model can call
# Add your own local tools here if any, or remove if there are no local tools
@tool
def calculate_age(birthdate_str: str):
    """Local tool that calucales the age of a person based on birthdate, in format %Y-%m-%d, e.g. 1978-10-29."""
    try:
        birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
        today = date.today()
        age = today.year - birthdate.year
        if (today.month, today.day) < (birthdate.month, birthdate.day):
            age -= 1
        logger.info(f"Calculated age for {birthdate}: {age}")
        return age
    except Exception as e:
        return 'Unknown'

# 2. Built-int tools, currently available options
# Add any built-in tools that the agent might need here, or keep empty if there are none
web_search_tool = {"type": "web_search_preview"}

## State of the agent
# This keeps the state of the agent across invocations
# Always keep messages, replace input, intermediate and result data with custom fields
class AgentState(TypedDict):
    # input data
    name: str 
    # intermediate data
    birthdate: str
    age: str

## Steps in the workflow.  Typically invoke the LLM with a specific prompt and set of tools
# Sample step that invokes the LLM with a built-in tool or MCP server, that are executed on the server-side
def do_step_one(state: AgentState):
    logger.info(f"Doing step one for data {state['name']}")
    # Invoke the LLM.  Make sure to create a prompt, and list any tools that might be needed
    prompt = f"Find the birthdate of {state['name']} in format %Y-%m-%d, e.g. 1978-10-29. Return only the date."
    step1_llm = llm.bind_tools([
        # you can also add mcp tools here, like:
        # {
        #     "type": "mcp",
        #     "server_label": "gitmcp",
        #     "server_url": "some_mcp_server_url_here",
        #     "require_approval": "never",
        # },
        # or built-in tools
        # web_search_tool,
    ])
    message = step1_llm.invoke(prompt)
    birthdate = message.content[0]['text']
    logger.info(f"Found date: {birthdate}")
    return {"birthdate": birthdate}

# Sample step that invokes the LLM with a local tool, that is executed in a local tool loop using a react agent
def do_step_two(state: AgentState):
    logger.info(f"Doing step one for data  {state['birthdate']}")
    agent = create_react_agent(
        llm,
        [
            calculate_age,
            # you can also add mcp tools here, like:
            # {
            #     "type": "mcp",
            #     "server_label": "gitmcp",
            #     "server_url": "some_mcp_server_url_here",
            #     "require_approval": "never",
            # },
            # or built-in tools
            # web_search_tool,
        ]
    )

    response = agent.invoke(
        {"messages": [{"role": "user", "content": f"""Calculate the age based on the birthdate.
            Use a tool to calculate (because current date is {date.today()}) and return only the result!
            Birthdate: {state['birthdate']}
            Age: """}]}
    )
    age = response['messages'][-1].content[0]['text']
    return {"age": age}
    

## Build the LangGraph workflow
workflow = StateGraph(AgentState)

workflow.add_node("step_one", do_step_one)
workflow.add_node("step_two", do_step_two)
workflow.add_edge(START, "step_one")
workflow.add_edge("step_one", "step_two")
workflow.add_edge("step_two", END)
agent = workflow.compile()

app = Flask(__name__, static_folder='.')

## Routes for the web UI
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/default-agent.png')
def default_agent_image():
    return send_from_directory('.', 'default-agent.png')

## Health endpoint, always keep this
@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

## Agent endpoint to trigger the agent, update to your use case
@app.route('/do_something', methods=['POST'])
def generate_abstract_endpoint():
    name = request.form.get('name')
    if not name:
        return jsonify({'error': 'No name provided'}), 400
    try:
        agentState = agent.invoke({"name": name})
        return jsonify({'result': agentState['age']})
    except Exception as e:
        logger.error(f"Error invoking agent: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='::')
