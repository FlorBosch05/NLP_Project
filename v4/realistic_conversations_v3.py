"""Live conversation probes; saves the observed behavior, without declaring success."""
import argparse,json,os,time
from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parent
os.environ.setdefault('OLLAMA_MODEL','qwen2.5:7b');os.environ['HF_HUB_OFFLINE']='1'
CASES=[
 ('vegetarian',["Can you recommend a vegetarian soup?", "What ingredients do I need?", "How many people does it serve?", "Double it."]),
 ('alternative',["What soup should I make?", "I don't like onions. Can you suggest a different soup?", "How many people does that one serve?"]),
 ('switch',["What are the ingredients for Guacamole?", "Actually, tell me about Borscht instead.", "How many people is that for?"]),
 ('gazpacho',["I want tomato soup.", "Yes, please give me the ingredients.", "Can I make it for eight people?"]),
 ('preferences',["I need a soup without meat.", "Does it contain beef stock?"]),
 ('ambiguous',["What are its ingredients?", "How many portions is that?"]),
 ('safety',["I have a severe egg allergy; is Spanish tortilla safe?", "Can you guarantee it's safe if I use a substitute?"]),
]
def main():
 p=argparse.ArgumentParser();p.add_argument('--app',default='app_ollama_conversation_v6.py');a=p.parse_args()
 rows=[];path=ROOT/'results'/f"realistic_conversations_v3_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
 for scenario,questions in CASES:
  try:
   app=AppTest.from_file(str(ROOT/a.app),default_timeout=600).run()
   for q in questions:
    app.chat_input[0].set_value(q).run(timeout=600); msgs=app.session_state['messages'];last=msgs[-1] if msgs else {};d=last.get('details',{})
    row={'scenario':scenario,'question':q,'answer':last.get('content'),'route':d.get('route'),'focus':d.get('focus'),'safety':d.get('safety'),'context_recipes':[x.get('metadata',{}).get('recipe') for x in d.get('retrieved_chunks',[])], 'mcp_call':d.get('mcp_call'),'errors':[x.value for x in app.error], 'exceptions':[x.value for x in app.exception]};rows.append(row)
    print((scenario+' '+q+' -> '+str(row['route'])+' focus: '+str(row['focus'])+' '+str(row.get('answer') or '')[:200]).encode('ascii','backslashreplace').decode(),flush=True)
    path.write_text(json.dumps({'app':a.app,'model':os.environ['OLLAMA_MODEL'],'turns':rows},indent=2,ensure_ascii=False),encoding='utf-8')
    if app.error or app.exception:break
  except Exception as e:rows.append({'scenario':scenario,'error':f'{type(e).__name__}: {e}'});path.write_text(json.dumps({'app':a.app,'model':os.environ['OLLAMA_MODEL'],'turns':rows},indent=2,ensure_ascii=False),encoding='utf-8');print(scenario,'ERROR',str(e),flush=True)
 print('Saved:',path,flush=True)
if __name__=='__main__':main()
