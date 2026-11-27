"""Check expected V4 evidence sections in the exact contexts sent to Ragas."""
import argparse,json,time
from pathlib import Path
from check_retrieval_v4 import LABELS
ROOT=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args()
 run=json.loads(a.run.read_text(encoding='utf-8')); rows=[]
 for case in run['cases']:
  if case['id'] not in LABELS:continue
  recipe,section=LABELS[case['id']]
  hits=[i for i,m in enumerate(case.get('context_metadata',[]),1) if m.get('recipe')==recipe and m.get('section')==section]
  rows.append({'id':case['id'],'recipe':recipe,'expected_section':section,'rank':hits[0] if hits else None,'chunks':case.get('context_metadata',[])})
 path=ROOT/'results'/f"ragas_context_audit_v1_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
 path.write_text(json.dumps({'source_run':str(a.run.resolve()),'note':'Project-authored section labels; presence of a section does not prove all claims are supported.','cases':rows},indent=2,ensure_ascii=False),encoding='utf-8')
 print('Expected section in provided context:',sum(r['rank'] is not None for r in rows),'/',len(rows));print('Missing:',[r['id'] for r in rows if r['rank'] is None]);print('Saved:',path)
if __name__=='__main__':main()
