"""Investigate the previous blocked tortilla response without publishing it in the UI."""
import json, os, time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1'; os.environ['TRANSFORMERS_OFFLINE']='1'
os.environ['LANGCHAIN_TRACING_V2']='false'; os.environ['LANGSMITH_TRACING']='false'
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from chef.agent_ollama_v4 import create_graph
from chef.retrieval import build_index
from chef.safety_rails_v2 import SafetyDecision, OUTPUT_SYSTEM

def main():
    q='How does the source say to prepare Spanish tortilla?'
    model=ChatOllama(model='qwen2.5:7b',base_url='http://127.0.0.1:11434',temperature=0,num_ctx=8192)
    graph=create_graph(build_index('sections'),model=model,top_k=5)
    result=graph.invoke({'question':q,'history':[]})
    payload=json.dumps({'question':q,'answer':result['answer']},ensure_ascii=False)
    detail={}
    try:
        response=model.with_structured_output(SafetyDecision,method='json_schema',include_raw=True).invoke([SystemMessage(content=OUTPUT_SYSTEM),HumanMessage(content=payload)])
        parsed=response.get('parsed'); detail={'category':parsed.category if parsed else None,'parsing_error':str(response.get('parsing_error')) if response.get('parsing_error') else None,'raw':str(getattr(response.get('raw'),'content',''))}
    except Exception as exc: detail={'exception':f'{type(exc).__name__}: {exc}'}
    root=Path(__file__).resolve().parent
    path=root/'results'/f"tortilla_diagnosis_v1_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
    path.write_text(json.dumps({'question':q,'draft':result['answer'],'classifier':detail,'note':'Private diagnostic draft; do not display as validated safe advice.'},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Classifier:',detail,'Saved:',path,flush=True)
if __name__=='__main__':main()
