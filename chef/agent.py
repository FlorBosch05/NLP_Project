"""A small stateful graph with retrieval and an MCP scaling tool."""
import asyncio
import json
import os
import sys
import time
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class State(TypedDict, total=False):
    question: str
    history: list
    route: str
    context: list
    tool_result: str
    answer: str
    usage: dict
    elapsed: float

def create_graph(index):
    model = ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"), temperature=0)
    def router(state):
        result = model.invoke([SystemMessage(content="Classify the request as exactly one word: scale, retrieve, or chat. Use scale for changing recipe servings, retrieve for recipe and dietary questions, chat for greetings. If scaling requires a recipe, choose scale."), HumanMessage(content=state["question"])])
        route = result.content.strip().lower().split()[0].strip(".,")
        return {"route": route if route in {"scale", "retrieve", "chat"} else "retrieve"}
    def retrieve(state):
        nodes = index.as_retriever(similarity_top_k=5).retrieve(state["question"])
        return {"context": [{"text": n.node.get_content(), "score": n.score, "metadata": n.node.metadata} for n in nodes]}
    async def call_scale(args):
        params = StdioServerParameters(command=sys.executable, args=["-m", "chef.mcp_server"], cwd=str(__import__('pathlib').Path(__file__).resolve().parent.parent))
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("scale_recipe", arguments=args)
                if result.isError:
                    raise ValueError("MCP scaling tool rejected the request")
                return str(result.structuredContent or [c.text for c in result.content if hasattr(c, "text")])
    def scale(state):
        schema = {"title":"ScalingRequest", "description":"Extract a recipe and the original and desired serving counts. Do not invent quantities.", "type":"object", "properties":{"ingredients":{"type":"array", "items":{"type":"object", "properties":{"name":{"type":"string"},"quantity":{"type":"number"},"unit":{"type":"string"}},"required":["name","quantity","unit"]}},"from_servings":{"type":"number"},"to_servings":{"type":"number"}},"required":["ingredients","from_servings","to_servings"]}
        try:
            msg = model.with_structured_output(schema).invoke([SystemMessage(content="Extract scaling inputs only from the user request and retrieved evidence. If any input is missing, return an empty ingredient list and zero for unknown serving counts."), HumanMessage(content=json.dumps({"question":state["question"],"context":state.get("context",[])}, ensure_ascii=False))])
            if not msg or not msg.get("ingredients") or msg.get("from_servings",0)<=0 or msg.get("to_servings",0)<=0:
                return {"tool_result":"Missing quantities or serving counts; ask the user for them."}
            return {"tool_result":asyncio.run(call_scale(msg))}
        except Exception as exc:
            return {"tool_result":f"Scaling unavailable: {type(exc).__name__}: {exc}. Ask the user for clarification or retry."}
    def answer(state):
        start=time.perf_counter()
        messages=[SystemMessage(content="You are a culinary assistant. Use provided recipe evidence and tool results; do not invent recipe facts or allergy guarantees. If evidence is insufficient, say so. Answer in the user's language." )]
        messages.extend(state.get("history", []))
        messages.append(HumanMessage(content=json.dumps({"question":state["question"],"retrieved_context":state.get("context",[]),"tool_result":state.get("tool_result")},ensure_ascii=False)))
        result=model.invoke(messages)
        return {"answer":result.content,"usage":result.usage_metadata or {},"elapsed":round(time.perf_counter()-start,3)}
    graph=StateGraph(State)
    for name, fn in [("route",router),("retrieve",retrieve),("scale",scale),("answer",answer)]: graph.add_node(name,fn)
    graph.add_edge(START,"route")
    graph.add_conditional_edges("route",lambda s:s["route"],{"chat":"answer","retrieve":"retrieve","scale":"retrieve"})
    graph.add_conditional_edges("retrieve",lambda s:s["route"],{"retrieve":"answer","scale":"scale"})
    graph.add_edge("scale","answer"); graph.add_edge("answer",END)
    return graph.compile()
