"""Run the existing 20-case V4 set on a specified local guarded graph."""
import argparse
import importlib
import json
import os
import time
from pathlib import Path

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['LANGCHAIN_TRACING_V2'] = 'false'
os.environ['LANGSMITH_TRACING'] = 'false'
from langchain_ollama import ChatOllama
from chef.agent_ollama_v4 import create_graph
from chef.retrieval import build_index

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--safety-module', default='chef.safety_rails_v2')
    parser.add_argument('--strategy', choices=['sections', 'recipe'], default='sections')
    parser.add_argument('--top-k', type=int, default=5)
    args = parser.parse_args()
    model_name = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')
    model = ChatOllama(model=model_name, base_url='http://127.0.0.1:11434', temperature=0, num_ctx=8192)
    guard = importlib.import_module(args.safety_module).GuardedGraph
    graph = guard(create_graph(build_index(args.strategy), model=model, top_k=args.top_k), model)
    cases = json.loads((ROOT/'data/evaluation_v4.json').read_text(encoding='utf-8'))
    path = ROOT/'results'/f"diagnostic_ollama_v1_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
    output = {'model': model_name, 'safety_module': args.safety_module, 'agent':'chef.agent_ollama_v4', 'strategy':args.strategy, 'top_k':args.top_k,
              'note':'Source-derived reference answers have not been independently reviewed. One fresh conversation per case.', 'cases':[]}
    for case in cases:
        started = time.perf_counter()
        row = {**case}
        try:
            r = graph.invoke({'question':case['question'], 'history':[]})
            row.update(actual_route=r.get('route'), route_correct=r.get('route')==case['expected_route'], answer=r.get('answer'),
                       contexts=[x['text'] for x in r.get('context',[])], context_metadata=[x['metadata'] for x in r.get('context',[])],
                       tool_call=r.get('tool_call'), tool_result=r.get('tool_result'), calls=r.get('calls',[]), safety=r.get('safety'))
            if 'expected_tool_result' in case:
                try: row['tool_correct'] = json.loads(r.get('tool_result') or 'null') == case['expected_tool_result']
                except (ValueError, TypeError): row['tool_correct'] = False
        except Exception as exc:
            row.update(error=f'{type(exc).__name__}: {exc}', route_correct=False)
        row['seconds'] = round(time.perf_counter()-started,3)
        output['cases'].append(row)
        path.write_text(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False),encoding='utf-8')
        print(case['id'],row.get('actual_route','ERROR'),'route',row['route_correct'],'tool',row.get('tool_correct','n/a'),flush=True)
    print('Saved:',path,flush=True)

if __name__ == '__main__': main()
