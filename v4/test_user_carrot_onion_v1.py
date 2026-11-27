"""Replay the user's Dutch carrot and English onion requests."""
import argparse,json,os,time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ.setdefault('OLLAMA_MODEL','qwen2.5:7b')
from streamlit.testing.v1 import AppTest
root=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--app',default='app_ollama_conversation_v15.py');a=p.parse_args();rows=[]
app=AppTest.from_file(str(root/a.app),default_timeout=600).run()
for q in ['geef me een recept met wortel','give me a recipe that uses onion']:
 app.chat_input[0].set_value(q).run(timeout=600);m=app.session_state['messages'][-1];d=m.get('details',{});row={'question':q,'answer':m.get('content'),'route':d.get('route'),'focus':d.get('focus'),'safety':d.get('safety'),'details':d,'errors':[x.value for x in app.error]};rows.append(row);print(json.dumps({k:row[k] for k in ('question','answer','route','focus','safety')},ensure_ascii=True),flush=True)
path=root/'results'/f"user_carrot_onion_v1_{Path(a.app).stem}_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json";path.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');print('Saved:',path,flush=True)
