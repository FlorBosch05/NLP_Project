"""Local Ollama V4 app; see INGREDIENT_EVIDENCE_v1.md."""
import os
import sys
import time
from pathlib import Path
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['LANGCHAIN_TRACING_V2'] = 'false'
os.environ['LANGSMITH_TRACING'] = 'false'
import streamlit as st
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT.parent / '.env')
from chef.retrieval import build_index
from chef.agent_ollama_v4 import create_graph
from chef.safety_rails_v8 import GuardedGraph
from chef.conversation_v7 import ConversationGraph

st.set_page_config(page_title='Flavor Chef V4', page_icon='🍲')
st.title('🍲 Flavor Chef')
st.caption('Version 4 · local Ollama · source: UniTools, CC BY-SA 4.0')
st.info('Recipe data: UniTools — theunitools.com, CC BY-SA 4.0. Source-provided times, dietary tags and instructions are not independently verified; check labels and cross-contact.')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')
OLLAMA_URL = 'http://127.0.0.1:11434'
st.caption(f'Local model: {OLLAMA_MODEL}')

@st.cache_resource(show_spinner='Loading the recipe index and assistant…')
def get_graph(strategy, top_k):
    model = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_URL, temperature=0, num_ctx=8192)
    index = build_index(strategy)
    return GuardedGraph(ConversationGraph(create_graph(index, model=model, top_k=top_k), index), model)

with st.sidebar:
    st.header('Retrieval')
    strategy = st.selectbox('Chunking strategy', ['sections', 'recipe'], help='Compare focused sections with complete recipes.')
    top_k = st.slider('Retrieved fragments', 1, 10, 5)
    if st.button('Clear conversation'):
        st.session_state.messages = []
        st.session_state.recipe_focus = None
        st.rerun()
    st.caption('Token counts exclude safety-classifier calls. Total time includes safety checks; time to first token refers to the final answer model call.')
    st.caption('Source traces can include vector-search results and separately labelled structured lookups.')

if 'messages' not in st.session_state: st.session_state.messages = []
if 'recipe_focus' not in st.session_state: st.session_state.recipe_focus = None
for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
        if 'details' in message:
            with st.expander('Sources, tools and measurements'):
                st.json(message['details'])
question = st.chat_input('Ask about a recipe or calculate a quantity')
if question:
    history = [{'role': m['role'], 'content': m['content']} for m in st.session_state.messages[-8:]]
    st.session_state.messages.append({'role': 'user', 'content': question})
    with st.chat_message('user'): st.markdown(question)
    with st.chat_message('assistant'):
        try:
            started = time.perf_counter()
            previous_scale = {}
            if st.session_state.messages and st.session_state.messages[-1]['role'] == 'user' and len(st.session_state.messages) >= 2:
                prior = st.session_state.messages[-2]
                call = prior.get('details', {}).get('mcp_call') or {}
                if prior.get('role') == 'assistant' and prior.get('content', '').startswith('Scaled ingredients for ') and call.get('name') == 'scale_recipe' and call.get('recipe_name'):
                    previous_scale = {'recipe_name': call['recipe_name'], 'target': call['arguments']['to_servings']}
            result = get_graph(strategy, top_k).invoke({'question': question, 'history': history, 'previous_scale': previous_scale, 'recipe_focus': st.session_state.recipe_focus})
            if 'recipe_focus' in result:
                st.session_state.recipe_focus = result['recipe_focus']
            elapsed = round(time.perf_counter() - started, 3)
            st.markdown(result['answer'])
            calls = result.get('calls', [])
            def total(field):
                values = [call.get(field) for call in calls]
                return sum(values) if values and all(v is not None for v in values) else None
            details = {'focus':st.session_state.recipe_focus, 'safety':result.get('safety'), 'route':result.get('route'), 'retrieval_query':result.get('search_query'), 'retrieved_chunks':result.get('context', []), 'mcp_call':result.get('tool_call'), 'mcp_result':result.get('tool_result'), 'model_calls':calls, 'total_input_tokens':total('input_tokens'), 'total_output_tokens':total('output_tokens'), 'answer_ttft_seconds':result.get('ttft_seconds'), 'total_seconds':elapsed, 'other_timings':result.get('timings', {})}
            with st.expander('Sources, tools and measurements'): st.json(details)
            st.session_state.messages.append({'role':'assistant','content':result['answer'],'details':details})
        except Exception as exc:
            st.error(f'Request failed: {type(exc).__name__}: {exc}')
