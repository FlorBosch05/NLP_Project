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
    latest={}; all_attempt_usage=[]
    for path in sorted((ROOT/'results').glob('ragas_qwen_v[12]_*.json'),key=lambda x:x.stat().st_mtime):
        batch=json.loads(path.read_text(encoding='utf-8'))
        if batch.get('judge_model')!=args.judge or Path(batch.get('source_run','')).resolve()!=source: continue
        for case in batch.get('cases',[]):
            if case['id'] in retrieval:
                usage=(case.get('judge_usage') or {}).get(args.judge,{}).get('total_tokens')
                if isinstance(usage,(float,int)): all_attempt_usage.append(usage)
                latest[case['id']]={'id':case['id'],'scores':case.get('scores',{}),'judge_usage':case.get('judge_usage'),'error':case.get('error'),'batch_file':path.name,'judge_max_output_tokens':batch.get('judge_max_output_tokens')}
    summary={}
    for metric in METRICS:
        values=[latest.get(i,{}).get('scores',{}).get(metric) for i in retrieval]
        valid=[x for x in values if isinstance(x,(float,int)) and math.isfinite(x)]
        summary[metric]={'scored':len(valid),'expected':len(retrieval),'mean_available':statistics.mean(valid) if valid else None,'missing_ids':[i for i,v in zip(retrieval,values) if not isinstance(v,(float,int)) or not math.isfinite(v)]}
    usages=[(latest[i].get('judge_usage') or {}).get(args.judge,{}).get('total_tokens') for i in retrieval if i in latest]
    reported=[x for x in usages if isinstance(x,(int,float))]
    result={'source_run':str(source),'judge_model':args.judge,'note':'Same answer run and judge only; Q13 was retried with a 900-token output cap. Most recent batch wins per case. Token totals are provider-reported and may exclude failed or unreported calls.','reported_judge_tokens_selected_cases':sum(reported),'reported_judge_tokens_all_attempts':sum(all_attempt_usage),'judge_usage_cases':len(reported),'scored_cases':len(latest),'summary':summary,'cases':[latest.get(i,{'id':i,'status':'not scored'}) for i in retrieval]}
    out=ROOT/'results'/f"ragas_summary_qwen_v2_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    print(json.dumps(summary,indent=2)); print('Reported judge tokens (selected cases):',sum(reported)); print('Reported judge tokens (all attempts):',sum(all_attempt_usage)); print('Saved:',out)

if __name__=='__main__': main()
