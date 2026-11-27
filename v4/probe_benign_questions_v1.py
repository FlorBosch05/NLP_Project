"""Probe varied ordinary culinary requests without treating any reply as correct."""
import argparse,json,os,time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ.setdefault('OLLAMA_MODEL','qwen2.5:7b')
from streamlit.testing.v1 import AppTest
root=Path(__file__).resolve().parent
QUESTIONS=['Hi, what can you help me cook?', 'What is an easy dinner idea?', 'Can you recommend something vegetarian?', 'I have potatoes and onions. What should I make?', 'How do I make Ratatouille?', 'Can you tell me about Bibimbap?', 'What are the ingredients in Gazpacho?', 'How many people does Borscht serve?', 'Can you suggest a soup without meat?', 'Which recipes contain garlic?', 'How much is 250 ml in litres?', 'What can I substitute for rabbit in Paella valenciana?', 'Is French onion soup served hot or cold?', 'I want something spicy, what do you suggest?', 'Hallo, wat kan ik koken met tomaten?', 'What is the difference between simmering and boiling?']
def main():
 p=argparse.ArgumentParser();p.add_argument('--app',default='app_ollama_conversation_v15.py');args=p.parse_args();rows=[];path=root/'results'/f"benign_questions_v1_{Path(args.app).stem}_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
 for q in QUESTIONS:
  try:
   app=AppTest.from_file(str(root/args.app),default_timeout=600).run();started=time.perf_counter();app.chat_input[0].set_value(q).run(timeout=600);m=app.session_state['messages'][-1];d=m.get('details',{});row={'question':q,'answer':m.get('content'),'route':d.get('route'),'focus':d.get('focus'),'safety':d.get('safety'),'wall_seconds':round(time.perf_counter()-started,2),'errors':[e.value for e in app.error],'exceptions':[e.value for e in app.exception]}
  except Exception as exc:row={'question':q,'error':f'{type(exc).__name__}: {exc}'}
  rows.append(row);path.write_text(json.dumps({'app':args.app,'model':os.environ['OLLAMA_MODEL'],'turns':rows},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(row,ensure_ascii=True),flush=True)
 print('Saved:',path,flush=True)
if __name__=='__main__':main()
