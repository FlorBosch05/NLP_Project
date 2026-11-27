"""Exercise retrieval controls and clear-conversation behavior in the live UI."""
import json,os,time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ.setdefault('OLLAMA_MODEL','qwen2.5:7b')
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parent

def main():
 cases=[]
 for strategy in ('sections','recipe'):
  for k in (1,5):
   try:
    app=AppTest.from_file(str(ROOT/'app_ollama_conversation_v10.py'),default_timeout=600).run()
    app.selectbox[0].select(strategy).run();app.slider[0].set_value(k).run()
    app.chat_input[0].set_value('What are the ingredients for Ratatouille?').run(timeout=600)
    d=app.session_state['messages'][-1].get('details',{});ctx=d.get('retrieved_chunks') or []
    vector=[x for x in ctx if x.get('metadata',{}).get('evidence_type')!='structured_lookup']
    direct=[x for x in ctx if x.get('metadata',{}).get('evidence_type')=='structured_lookup']
    errors=[]
    if app.error or app.exception or d.get('route')!='retrieve':errors.append('UI or route failure')
    if len(vector)>k:errors.append(f'asked for {k} search results but received {len(vector)}')
    if len(direct)!=1:errors.append('missing structured record')
    if strategy=='recipe' and any(x.get('metadata',{}).get('section')!='recipe' for x in vector):errors.append('wrong chunking strategy')
    next(x for x in app.button if x.label=='Clear conversation').click().run()
    if app.session_state['messages'] or app.session_state['recipe_focus'] is not None:errors.append('conversation did not clear')
    cases.append({'strategy':strategy,'top_k':k,'vector_count':len(vector),'structured_count':len(direct),'problems':errors})
   except Exception as exc:cases.append({'strategy':strategy,'top_k':k,'problems':[f'{type(exc).__name__}: {exc}']})
   print(strategy,k,'PASS' if not cases[-1]['problems'] else 'FAIL: '+', '.join(cases[-1]['problems']),flush=True)
 path=ROOT/'results'/f"final_settings_v2_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
 path.write_text(json.dumps({'app':'app_ollama_conversation_v10.py','cases':cases},indent=2),encoding='utf-8');print('Saved:',path,flush=True)
 if any(c['problems'] for c in cases):raise SystemExit(1)
if __name__=='__main__':main()
