"""Replay the reported soup conversation through a chosen Streamlit version."""
import argparse,json,os,time
from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parent
os.environ.setdefault('OLLAMA_MODEL','qwen2.5:7b')
os.environ['HF_HUB_OFFLINE']='1'

def main():
    p=argparse.ArgumentParser();p.add_argument('--app',default='app_ollama_safety_v5.py');args=p.parse_args()
    questions=['yooo gamer, what soup should i make today','no restrictions just a salty soup','how many people is that recipe for','we were talking about tomato soup though']
    app=AppTest.from_file(str(ROOT/args.app),default_timeout=600).run(); rows=[]
    for q in questions:
        try:
            app.chat_input[0].set_value(q).run(timeout=600)
            last=app.session_state['messages'][-1];d=last.get('details',{})
            rows.append({'question':q,'answer':last.get('content'),'route':d.get('route'),'safety':d.get('safety'),'retrieved_chunks':d.get('retrieved_chunks'), 'focus':d.get('focus'),'errors':[x.value for x in app.error], 'exceptions':[x.value for x in app.exception]})
        except Exception as exc: rows.append({'question':q,'error':f'{type(exc).__name__}: {exc}'})
        print(q,'->',rows[-1].get('route',rows[-1].get('error')),'answer:',str(rows[-1].get('answer',''))[:120].encode('ascii','backslashreplace').decode(),flush=True)
    path=ROOT/'results'/f"soup_conversation_v1_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
    path.write_text(json.dumps({'app':args.app,'model':os.environ['OLLAMA_MODEL'],'turns':rows},indent=2,ensure_ascii=False),encoding='utf-8');print('Saved:',path,flush=True)
if __name__=='__main__':main()
