"""Score saved local answers in resumable, separately saved Ragas batches."""
import argparse
import json
import math
import os
import time
from pathlib import Path
os.environ['LANGCHAIN_TRACING_V2']='false'
os.environ['LANGSMITH_TRACING']='false'
from langchain_ollama import ChatOllama
from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import LLMContextPrecisionWithReference, LLMContextRecall, Faithfulness
from ragas.run_config import RunConfig

ROOT=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(); p.add_argument('run',type=Path); p.add_argument('--offset',type=int,default=0); p.add_argument('--limit',type=int,default=1); args=p.parse_args()
    data=json.loads(args.run.read_text(encoding='utf-8'))
    cases=[c for c in data['cases'] if c.get('expected_route')=='retrieve' and c.get('actual_route')=='retrieve' and c.get('contexts') and c.get('answer')]
    selected=cases[args.offset:args.offset+args.limit]
    output={'source_run':str(args.run.resolve()),'judge':'qwen2.5:7b','note':'Local generator and judge use the same model. Blocked cases are excluded, not treated as passes. References are not independently verified.', 'cases':[]}
    path=ROOT/'results'/f"ragas_ollama_diagnostic_v2_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
    for case in selected:
        row={'id':case['id']}
        # Each evaluate call owns an event loop; a new client avoids reusing a closed loop.
        judge=LangchainLLMWrapper(ChatOllama(model=os.getenv('OLLAMA_MODEL','qwen2.5:7b'), base_url='http://127.0.0.1:11434', temperature=0,num_ctx=8192,num_predict=1024))
        try:
            sample=SingleTurnSample(user_input=case['question'],reference=case['reference'],response=case['answer'],retrieved_contexts=case['contexts'])
            scored=evaluate(EvaluationDataset(samples=[sample]), metrics=[LLMContextPrecisionWithReference(),LLMContextRecall(),Faithfulness()], llm=judge, run_config=RunConfig(max_workers=1,max_retries=1,timeout=180),raise_exceptions=False)
            row['scores']=json.loads(scored.to_pandas().to_json(orient='records'))[0]
        except Exception as exc: row['error']=f'{type(exc).__name__}: {exc}'
        output['cases'].append(row); path.write_text(json.dumps(output,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
        print(case['id'], 'scores', {k:v for k,v in row.get('scores',{}).items() if k in ('llm_context_precision_with_reference','context_recall','faithfulness')}, 'error',row.get('error'),flush=True)
    print('Saved:',path,flush=True)

if __name__=='__main__': main()
