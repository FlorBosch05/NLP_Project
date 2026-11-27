"""Investigate rejected local-model drafts; output is saved locally."""
import os,sys,json,time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root))
from langchain_ollama import ChatOllama
from chef.retrieval import build_index
from chef.agent_ollama_v4 import create_graph
from chef.conversation_v8 import ConversationGraph
from chef.safety_checks_v5 import check_input,check_output
m=ChatOllama(model='qwen2.5:7b',base_url='http://127.0.0.1:11434',temperature=0,num_ctx=8192)
i=build_index('sections');g=ConversationGraph(create_graph(i,model=m,top_k=5),i,top_k=5)
rows=[]
for q in ['spaghetti','onion soup','i want something with carrots give me a recipe']:
 try:
  state={'question':q,'history':[],'recipe_focus':None};result=g.invoke(state);answer=result.get('answer',''); rows.append({'question':q,'answer':answer,'route':result.get('route'),'input':check_input(m,q,[]),'output':check_output(m,q,answer)})
 except Exception as e:rows.append({'question':q,'error':str(e)})
 print(json.dumps(rows[-1],ensure_ascii=True),flush=True)
p=root/'results'/f"guard_draft_v1_{time.strftime('%Y%m%d_%H%M%S')}.json";p.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');print(p)
