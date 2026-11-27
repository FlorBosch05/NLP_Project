"""Replay the reported conversation against a selected app and save the trace."""
import argparse, json, os, time
from pathlib import Path
from streamlit.testing.v1 import AppTest
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
os.environ.setdefault('OLLAMA_MODEL','qwen2.5:7b')
root=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--app',default='app_ollama_conversation_v10.py');args=p.parse_args()
app=AppTest.from_file(str(root/args.app),default_timeout=600).run()
rows=[]
for q in ['spagettie','spaghetti','what soup should i eat today','ok onino soup','onion soup','i want something with carrots give me a recipe']:
    app.chat_input[0].set_value(q).run(timeout=600)
    m=app.session_state['messages'][-1]; d=m.get('details',{})
    row={'question':q,'answer':m.get('content'),'route':d.get('route'),'focus':d.get('focus'),'safety':d.get('safety')}
    rows.append(row); print(json.dumps(row,ensure_ascii=True),flush=True)
path=root/'results'/f"user_chat_v1_{Path(args.app).stem}_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
path.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8'); print('Saved:',path,flush=True)
