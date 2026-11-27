"""Additional live final-app probes; source-specific assertions and saved evidence."""
import json,os,time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ.setdefault('OLLAMA_MODEL','qwen2.5:7b')
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parent
CASES=[
 ('substitution','What substitute does the source suggest for rabbit in Paella valenciana?'),
 ('cross_dimension','Convert 250 g to cups.'),
 ('zero_servings','Scale Guacamole to 0 servings.'),
 ('onion_free',"I don't like onions. Can you recommend a soup?"),
 ('named_servings','How many people does Borscht serve?'),
 ('dutch_ingredients','Wat zijn de ingrediënten van Guacamole?'),
]
def main():
 recipes={r['name']:r for r in json.loads((ROOT/'data/recipes_v4.json').read_text(encoding='utf-8'))};rows=[]
 for ident,q in CASES:
  try:
   app=AppTest.from_file(str(ROOT/'app_ollama_conversation_v10.py'),default_timeout=600).run();app.chat_input[0].set_value(q).run(timeout=600)
   last=app.session_state['messages'][-1];details=last.get('details',{});answer=last.get('content','');route=details.get('route');focus=details.get('focus');problems=[]
   if app.error or app.exception or last.get('role')!='assistant':problems.append('UI error')
   if ident=='substitution' and (route!='retrieve' or 'chicken' not in answer.casefold()):problems.append('source substitution not answered')
   if ident=='cross_dimension':
    tool=details.get('mcp_result') or ''; 
    if route=='convert' and not (str(tool).startswith('Tool failed:') or str(tool).startswith('Please provide')):problems.append('mass-to-volume conversion returned as if supported')
    elif route!='convert' and not any(w in answer.casefold() for w in ('cannot','can\'t','unable','density','need','which','not')):problems.append('unsupported conversion not explained')
   if ident=='zero_servings' and (details.get('mcp_call') or 'servings' not in answer.casefold()):problems.append('invalid target not clarified')
   if ident=='onion_free' and (focus not in recipes or any('onion' in i['name'].casefold() for i in recipes[focus]['ingredients'])):problems.append('onion-free preference not honored')
   if ident=='named_servings' and ('6' not in answer or focus!='Borscht'):problems.append('wrong serving count or focus')
   if ident=='dutch_ingredients' and ('avocado' not in answer.casefold() or focus!='Guacamole'):problems.append('Dutch ingredient lookup failed')
   rows.append({'id':ident,'question':q,'answer':answer,'route':route,'focus':focus,'tool_result':details.get('mcp_result'),'problems':problems})
  except Exception as exc:rows.append({'id':ident,'problems':[f'{type(exc).__name__}: {exc}']})
  print(ident,'PASS' if not rows[-1]['problems'] else 'FAIL: '+', '.join(rows[-1]['problems']),flush=True)
 path=ROOT/'results'/f"final_extra_cases_v1_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
 path.write_text(json.dumps({'app':'app_ollama_conversation_v10.py','cases':rows},indent=2,ensure_ascii=False),encoding='utf-8');print('Saved:',path,flush=True)
 if any(r['problems'] for r in rows):raise SystemExit(1)
if __name__=='__main__':main()
