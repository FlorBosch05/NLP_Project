"""Summarize one source run and one judge; missing metrics remain missing."""
import argparse
import json
import math
import statistics
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
METRICS=('llm_context_precision_with_reference','context_recall','faithfulness')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('run',type=Path)
    p.add_argument('--judge',required=True)
    args=p.parse_args()
    source=args.run.resolve()
    run=json.loads(source.read_text(encoding='utf-8'))
    retrieval=[c['id'] for c in run['cases'] if c.get('expected_route')=='retrieve' and c.get('contexts') and c.get('answer')]
    latest={}
    for path in sorted((ROOT/'results').glob('ragas_batch_*.json'),key=lambda x:x.stat().st_mtime):
        batch=json.loads(path.read_text(encoding='utf-8'))
        if batch.get('judge_model')!=args.judge or Path(batch.get('source_run','')).resolve()!=source: continue
        for case in batch.get('cases',[]):
            if case['id'] in retrieval: latest[case['id']]={'id':case['id'],'scores':case.get('scores',{}),'error':case.get('error'),'batch_file':path.name}
    summary={}
    for metric in METRICS:
        values=[latest.get(i,{}).get('scores',{}).get(metric) for i in retrieval]
        valid=[x for x in values if isinstance(x,(float,int)) and math.isfinite(x)]
        summary[metric]={'scored':len(valid),'expected':len(retrieval),'mean_available':statistics.mean(valid) if valid else None,'missing_ids':[i for i,v in zip(retrieval,values) if not isinstance(v,(float,int)) or not math.isfinite(v)]}
    result={'source_run':str(source),'judge_model':args.judge,'note':'Means use only available values and are not comparable to complete benchmarks. Most recent batch wins for each case.','summary':summary,'cases':[latest.get(i,{'id':i,'status':'not scored'}) for i in retrieval]}
    out=ROOT/'results'/f"ragas_summary_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    print(json.dumps(summary,indent=2)); print('Saved:',out)

if __name__=='__main__': main()
