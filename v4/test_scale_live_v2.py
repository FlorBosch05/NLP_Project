"""Live Qwen regression checks for the separate V4 scaling-display fix."""
import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from chef.agent_scale_v3 import create_graph
from chef.retrieval import build_index, read_recipes

ROOT=Path(__file__).resolve().parent
load_dotenv(ROOT.parent/'.env')
os.environ['GROQ_MODEL']='qwen/qwen3.8-27b'
CASES=[
    {'id':'L01','question':'Scale Ratatouille from 4 to 8 servings.','recipe':'Ratatouille','target':8,'history':[]},
    {'id':'L02','question':'Scale Ratatouille please.','recipe':'Ratatouille','target':None,'history':[]},
]

def validate(result,case,recipe):
    problems=[]
    if result.get('route')!='scale': problems.append('wrong route')
    call=result.get('tool_call') or {}
    if case['target'] is None:
        if call: problems.append('tool called without requested servings')
        if result.get('answer')!='How many servings would you like?': problems.append('unclear clarification')
        return problems
    if call.get('name')!='scale_recipe': return problems+['scaling tool not called']
    args=call.get('arguments',{})
    if args.get('to_servings')!=case['target'] or args.get('from_servings')!=recipe['servings']: problems.append('wrong serving counts')
    try: items=json.loads(result.get('tool_result',''))['result']
    except (ValueError,KeyError,TypeError): return problems+['invalid tool result']
    if len(items)!=len(recipe['ingredients']): return problems+['ingredient count mismatch']
    factor=case['target']/recipe['servings']
    for src,out in zip(recipe['ingredients'],items):
        if out.get('name')!=src['name'] or out.get('unit')!=str(src['unit']): problems.append('ingredient mismatch: '+src['name']);continue
        q,rule=src['quantity'],src['scaling']
        if q is None or rule=='damped':
            if out.get('quantity') is not None: problems.append('manual quantity invented: '+src['name'])
        else:
            expected=round(q*factor,3) if rule=='linear' else q
            if out.get('quantity')!=expected: problems.append('wrong quantity: '+src['name'])
        if src['name'] not in result.get('answer',''): problems.append('ingredient missing from display: '+src['name'])
    if 'Source cooking steps may contain quantities and timings for the original servings' not in result.get('answer',''): problems.append('missing unscaled-steps warning')
    return problems

def main():
    recipes={x['name']:x for x in read_recipes()}
    graph=create_graph(build_index('sections'))
    rows=[]
    for case in CASES:
        try:
            result=graph.invoke({'question':case['question'],'history':case['history']})
            problems=validate(result,case,recipes[case['recipe']])
            rows.append({'case':case,'route':result.get('route'),'tool_call':result.get('tool_call'),'tool_result':result.get('tool_result'),'answer':result.get('answer'),'calls':result.get('calls',[]),'problems':problems})
        except Exception as exc:
            rows.append({'case':case,'error':f'{type(exc).__name__}: {exc}','problems':['request failed']})
        print(case['id'],'PASS' if not rows[-1]['problems'] else 'FAIL',flush=True)
        if 'RateLimitError' in rows[-1].get('error','') and ('tokens per day' in rows[-1]['error'] or 'TPD' in rows[-1]['error']):
            print('Daily quota reached; remaining cases not attempted.',flush=True);break
    path=ROOT/'results'/f"scaling_live_qwen_v2_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
    path.write_text(json.dumps({'model':os.environ['GROQ_MODEL'],'agent':'agent_scale_v3','cases':rows},indent=2,ensure_ascii=False),encoding='utf-8')
    print('Saved:',path,flush=True)

if __name__=='__main__': main()
