import os
import sys
from pathlib import Path

# Windows consoles default to cp1252, which cannot print emoji from LLM replies
sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

# 1. SETUP & PATH RESOLUTION

script_dir=Path(__file__).resolve().parent
project_root=script_dir.parents[0]

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.agent_tool import query_telemetry_db, fetch_corridor_conditions, search_compliance_sop

load_dotenv(project_root / ".env")

class AgentState(TypedDict):
   messages:Annotated[list[BaseMessage], add_messages]


# 2. FACTORY INITIALIZATION: AGENT REASONER LLM

AGENT_LLM_SETTING=os.getenv("AGENT_LLM", "ANTHROPIC").strip().upper()

if AGENT_LLM_SETTING=="ANTHROPIC":
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise ValueError("Missing ANTHROPIC_API_KEY in .env")
    print("Brain Mode : Utilizing Anthropic LLM")
    from langchain_anthropic import ChatAnthropic
    agent_llm=ChatAnthropic(model_name="claude-sonnet-4-6", temperature=0.0, max_tokens=1024)

fde_tools=[query_telemetry_db, fetch_corridor_conditions, search_compliance_sop]
llm_with_tools=agent_llm.bind_tools(fde_tools)


# 3. Graph ARCHITECTURE ASSEMBLY
def reasoning_node(state:AgentState):
    """
    This node represents the reasoning step of the agent.
    It takes the current state of the agent and produces a response based on the tools and LLM.
    """
    response=llm_with_tools.invoke(state["messages"])
    return {"messages":[response]}

print("Compliling LangGrapth FDE Orchestrator")
graph_builder=StateGraph(AgentState)
graph_builder.add_node("reasoner",reasoning_node)
graph_builder.add_node("tools", ToolNode(fde_tools))

graph_builder.add_edge(START, "reasoner")
graph_builder.add_conditional_edges("reasoner",tools_condition)
graph_builder.add_edge("tools", "reasoner")

fde_agent=graph_builder.compile(checkpointer=MemorySaver())

# 4. CHAT LOOP TESTING PANNEL
if __name__=="__main__":
    print("\n" + "="*55)
    print("FDE Supply Chain Orchestrator State Machine Online")
    print(f"Configured Execution: [LLM: {AGENT_LLM_SETTING}] -> [Embedding: {os.getenv('Embedding_Model', 'LOCAL')}]")
    print("="*55 + "\n")

    prompt_path=project_root / "src" / "prompts" / "system.prompt.txt"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_instruction=f.read()
    except FileNotFoundError:
        print(f"System prompt file not found at {prompt_path}. Please ensure the file exists.")
        system_instruction="You are an AI agent designed to assist with supply chain operations. You have access to various tools and databases to provide accurate and timely information."

    system_prompt=SystemMessage(content=system_instruction)
    thread_config={"thread_id":"production_test_1"}
    is_first_turn=True

    while True:
        user_input=input("\nDispatcher> ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting FDE Orchestrator. Goodbye!")
            break

        new_messages=[("user", user_input)]
        if is_first_turn:
            new_messages.insert(0, system_prompt)
            is_first_turn=False
        events=fde_agent.stream({"messages": new_messages}, config=thread_config)
        for event in events:
            for node_name, node_state in event.items():
                if node_name=="tools":
                   print("[System] Retriving external data elements via ToolNode")
                elif node_name=="reasoner":
                    latest_msg=node_state["messages"][-1]  
                    if latest_msg.content:
                        print(f"[Reasoner Node] Latest Message: {latest_msg.content}") 



