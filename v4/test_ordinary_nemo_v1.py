"""Live ordinary questions that previously produced wrong or blocked replies."""
import json,os,time,sys
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ.setdefault('OLLAMA_MODEL','qwen2.5:7b')
from streamlit.testing.v1 import AppTest
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root))
from chef.recipe_catalog_v4 import ingredient_in_record
recipes={r['name']:r for r in json.loads((root/'data/recipes_v4.json').read_text(encoding='utf-8'))}
questions=['Can you tell me about Bibimbap?','What is the difference between simmering and boiling?','Hallo, wat kan ik koken met tomaten?','geef me een recept met wortel','give me a recipe that uses onion']
rows=[]
for q in questions:
 app=AppTest.from_file(str(root/'app_ollama_conversation_v17.py'),default_timeout=600).run();start=time.perf_counter();app.chat_input[0].set_value(q).run(timeout=600);m=app.session_state['messages'][-1];d=m.get('details',{});answer=m.get('content','');focus=d.get('focus');route=d.get('route');problems=[]
 if app.error or app.exception:problems.append('UI error')
 if route in ('safety_block','error'):problems.append('ordinary question blocked')
 if q.startswith('Can you tell') and (focus!='Bibimbap' or 'Bibimbap' not in answer):problems.append('missing named recipe overview')
 if q.startswith('What is the difference') and not all(w in answer.casefold() for w in ('simmer','boil')):problems.append('comparison not answered')
 if 'tomaten' in q:
  sources={c.get('metadata',{}).get('recipe') for c in d.get('retrieved_chunks',[]) if c.get('metadata',{}).get('evidence_type')=='structured_lookup'}
  selected=[recipes[s] for s in sources if s in recipes]
  if not selected or any(not ingredient_in_record(r,'tomato') for r in selected):problems.append('missing grounded tomato matches')
 if 'wortel' in q and (focus!='Borscht' or 'Wortel' not in answer or 'Bereiding' not in answer):problems.append('Dutch carrot recipe incorrect')
 if q=='give me a recipe that uses onion' and (focus not in recipes or not ingredient_in_record(recipes[focus],'onion') or 'Preparation' not in answer):problems.append('onion recipe incomplete')
 row={'question':q,'answer':answer,'route':route,'focus':focus,'safety':d.get('safety'),'details':d,'wall_seconds':round(time.perf_counter()-start,2),'problems':problems};rows.append(row);print('PASS' if not problems else 'FAIL '+str(problems),json.dumps({'question':q,'answer':answer,'safety':d.get('safety')},ensure_ascii=True),flush=True)
p=root/'results'/f"ordinary_nemo_v1_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json";p.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');print('Saved:',p,flush=True)
if any(r['problems'] for r in rows):raise SystemExit(1)
