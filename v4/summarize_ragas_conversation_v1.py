"""Summarize Ragas without hiding missing scores or excluded cases."""
import argparse,json,statistics,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
METRICS=('llm_context_precision_with_reference','context_recall','faithfulness')
def main():
 p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('ragas',type=Path);a=p.parse_args()
 run=json.loads(a.source.read_text(encoding='utf-8'));scored=json.loads(a.ragas.read_text(encoding='utf-8'))
 expected=[c['id'] for c in run['cases'] if c.get('expected_route')=='retrieve']
 cases={c['id']:c for c in scored.get('cases',[])}
 result={'source_run':str(a.source.resolve()),'ragas_run':str(a.ragas.resolve()),'generation_model':run.get('model'),'judge':scored.get('judge'),'expected_retrieval_cases':expected,'summary':{},'excluded_or_missing': [i for i in expected if i not in cases]}
 for metric in METRICS:
  values=[c.get('scores',{}).get(metric) for c in cases.values()]; nums=[v for v in values if isinstance(v,(int,float))]
  missing=[i for i in expected if i not in cases or cases[i].get('scores',{}).get(metric) is None]
  result['summary'][metric]={'scored':len(nums),'expected':len(expected),'mean_available':statistics.mean(nums) if nums else None,'missing_ids':missing}
 result['case_scores']=[{'id':i,'scores':{m:cases.get(i,{}).get('scores',{}).get(m) for m in METRICS},'error':cases.get(i,{}).get('error')} for i in expected]
 path=ROOT/'results'/f"ragas_conversation_summary_v1_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
 path.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
 print(json.dumps(result['summary'],indent=2));print('Saved:',path)
if __name__=='__main__':main()
