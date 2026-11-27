"""Run saved golden cases and Ragas on cases that expect recipe retrieval."""
import argparse
import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import LLMContextPrecisionWithReference, LLMContextRecall, Faithfulness
from ragas.run_config import RunConfig
from chef.agent import create_graph
from chef.retrieval import build_index

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent / '.env')
os.environ['GROQ_MODEL']='qwen/qwen3.8-27b'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--strategy', choices=['sections','recipe'], default='sections')
    parser.add_argument('--top-k', type=int, default=5)
    parser.add_argument('--offset', type=int, default=0, help='Skip this many cases before applying --limit')
    parser.add_argument('--limit', type=int, default=0, help='Limit to the first N cases; zero means all')
    parser.add_argument('--no-ragas', action='store_true', help='Run routes and answers without Ragas scoring')
    args=parser.parse_args()
    cases=json.loads((ROOT/'data'/'evaluation_v4.json').read_text(encoding='utf-8'))
    if args.offset < 0 or args.limit < 0: parser.error('offset and limit must be non-negative')
    cases=cases[args.offset:]
    if args.limit: cases=cases[:args.limit]
    graph=create_graph(build_index(args.strategy), top_k=args.top_k)
    records=[]; samples=[]
    stopped_reason=None
    for case in cases:
        started=time.perf_counter()
        try:
            r=graph.invoke({'question':case['question'],'history':[]})
            record={**case, 'actual_route':r.get('route'), 'route_correct':r.get('route')==case['expected_route'], 'answer':r.get('answer'), 'contexts':[x['text'] for x in r.get('context',[])], 'tool_call':r.get('tool_call'), 'tool_result':r.get('tool_result'), 'calls':r.get('calls',[]), 'seconds':round(time.perf_counter()-started,3)}
            if 'expected_tool_result' in case:
                try:
                    record['tool_correct'] = json.loads(record['tool_result'] or 'null') == case['expected_tool_result']
                except (ValueError, TypeError):
                    record['tool_correct'] = False
            if case['expected_route']=='retrieve' and record['contexts']:
                samples.append(SingleTurnSample(user_input=case['question'], reference=case['reference'], response=record['answer'], retrieved_contexts=record['contexts']))
        except Exception as exc:
            record={**case, 'error':f'{type(exc).__name__}: {exc}', 'route_correct':False}
        records.append(record)
        print(case['id'], 'route:',record.get('actual_route','ERROR'), flush=True)
        if 'RateLimitError' in record.get('error','') and ('tokens per day' in record['error'] or 'TPD' in record['error']):
            stopped_reason='Groq daily token quota reached; remaining cases were not attempted.'
            print(stopped_reason, flush=True)
            break
    output={'generation_model':os.environ['GROQ_MODEL'], 'strategy':args.strategy, 'top_k':args.top_k, 'offset':args.offset, 'cases':records, 'ragas':None}
    if stopped_reason: output['stopped_reason']=stopped_reason
    path=ROOT/'results'/f"evaluation_qwen_v1_{args.strategy}_k{args.top_k}_{time.strftime('%Y%m%d_%H%M%S')}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(output,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    if samples and not args.no_ragas and not stopped_reason:
        try:
            judge=LangchainLLMWrapper(ChatGroq(model=os.getenv('GROQ_MODEL','openai/gpt-oss-20b'),temperature=0))
            scored=evaluate(EvaluationDataset(samples=samples), metrics=[LLMContextPrecisionWithReference(),LLMContextRecall(),Faithfulness()], llm=judge, run_config=RunConfig(max_workers=1, max_retries=3, timeout=180), raise_exceptions=False)
            output['ragas'] = json.loads(scored.to_pandas().to_json(orient='records'))
        except Exception as exc:
            output['ragas_error'] = f'{type(exc).__name__}: {exc}'
        path.write_text(json.dumps(output,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    print('Saved:',path)

if __name__=='__main__': main()
