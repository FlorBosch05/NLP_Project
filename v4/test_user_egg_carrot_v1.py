"""Replay user conversation in a selected application and retain every result."""
import argparse,json,os,time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ.setdefault('OLLAMA_MODEL','qwen2.5:7b')
from streamlit.testing.v1 import AppTest
root=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--app',default='app_ollama_conversation_v12.py');args=p.parse_args()
app=AppTest.from_file(str(root/args.app),default_timeout=600).run();rows=[]
for q in ['give me a recipe with eggs','do you have any other recipes with eggs?','i want a list of egg having recipes','any recipes with carrot?','ok give me the recipe for bibimbap']:
 app.chat_input[0].set_value(q).run(timeout=600);m=app.session_state['messages'][-1];d=m.get('details',{})
 row={'question':q,'answer':m.get('content'),'route':d.get('route'),'focus':d.get('focus'),'safety':d.get('safety'),'errors':[e.value for e in app.error]}
 rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
path=root/'results'/f"user_egg_carrot_v1_{Path(args.app).stem}_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json";path.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');print('Saved:',path,flush=True)
