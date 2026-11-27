"""Live probe of a benign negative preference, including NeMo timing metadata."""
import json,os,time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ.setdefault('OLLAMA_MODEL','qwen2.5:7b')
from streamlit.testing.v1 import AppTest
root=Path(__file__).resolve().parent;app=AppTest.from_file(str(root/'app_ollama_conversation_v17.py'),default_timeout=600).run();rows=[]
for q in ['I dislike carrots; suggest a recipe.','I would rather have a dish without onions.']:
 start=time.perf_counter();app.chat_input[0].set_value(q).run(timeout=600);m=app.session_state['messages'][-1];d=m.get('details',{});row={'question':q,'answer':m.get('content'),'route':d.get('route'),'safety':d.get('safety'),'wall_seconds':round(time.perf_counter()-start,2),'details':d};rows.append(row);print(json.dumps({k:row[k] for k in ('question','answer','route','safety','wall_seconds')},ensure_ascii=True),flush=True)
p=root/'results'/f"negative_preference_v1_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json";p.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');print('Saved:',p,flush=True)
