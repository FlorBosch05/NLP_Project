import os
import time
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from chef.retrieval import build_index
from chef.agent import create_graph

load_dotenv()
st.set_page_config(page_title="Flavor Chef", page_icon="🍲")
st.title("🍲 Flavor Chef")
st.caption("Recepten zoeken en porties berekenen met een lokale kennisbank en MCP.")
if not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") == "your_key_here":
    st.info("Voeg je GROQ_API_KEY toe aan het bestand .env om te beginnen.")
    st.stop()
@st.cache_resource
def graph(): return create_graph(build_index())
if "messages" not in st.session_state: st.session_state.messages=[]
for item in st.session_state.messages:
    with st.chat_message(item["role"]): st.markdown(item["content"])
question=st.chat_input("Stel een vraag over recepten of porties")
if question:
    history=[HumanMessage(content=m["content"]) if m["role"]=="user" else AIMessage(content=m["content"]) for m in st.session_state.messages[-8:]]
    st.session_state.messages.append({"role":"user","content":question})
    with st.chat_message("user"): st.markdown(question)
    with st.chat_message("assistant"):
        try:
            start=time.perf_counter(); result=graph().invoke({"question":question,"history":history}); total=time.perf_counter()-start
            st.markdown(result["answer"])
            with st.expander("Bronnen, routing en metingen"):
                st.write("Route:",result.get("route")); st.write("Gevonden fragmenten:",result.get("context",[])); st.write("MCP-resultaat:",result.get("tool_result","Geen tool aangeroepen")); st.write("Tokens laatste modelaanroep:",result.get("usage",{})); st.write(f"Totale tijd: {total:.2f} s; antwoordgeneratie: {result['elapsed']:.2f} s")
            st.session_state.messages.append({"role":"assistant","content":result["answer"]})
        except Exception as e: st.error(f"De aanvraag is mislukt: {e}")
