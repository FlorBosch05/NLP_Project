"""Test context, restrictions and subsequent explicit recipe requests."""
import json,os,sys,time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ.setdefault('OLLAMA_MODEL','qwen2.5:7b')
from streamlit.testing.v1 import AppTest
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root))
from chef.recipe_catalog_v4 import ingredient_in_record
recipes={r['name']:r for r in json.loads((root/'data/recipes_v4.json').read_text(encoding='utf-8'))}
scenarios=[('positive_then_exclude',["I've got carrots; what dish can I make?",'without onions please']),
 ('persistent_preference',["I dislike onions; suggest a recipe.",'give me a recipe with carrots']),
 ('conflicting_named',["I dislike onions; suggest a recipe.",'give me the recipe for French onion soup']),
 ('soup_context',['hey, I feel like soup tonight. Any ideas?','something without onions please','sounds good, what do I need?'])]
rows=[]
for name,turns in scenarios:
 app=AppTest.from_file(str(root/'app_ollama_conversation_v17.py'),default_timeout=600).run()
 for pos,q in enumerate(turns):
  start=time.perf_counter();app.chat_input[0].set_value(q).run(timeout=600);m=app.session_state['messages'][-1];d=m.get('details',{});answer=m.get('content','');focus=d.get('focus');route=d.get('route');recipe=recipes.get(focus);problems=[]
  if app.error or app.exception:problems.append('UI error')
  if name in ('positive_then_exclude','persistent_preference') and pos==1:
   if route!='retrieve' or not recipe or not ingredient_in_record(recipe,'carrot') or ingredient_in_record(recipe,'onion'):problems.append('prior preference or ingredient not preserved')
  if name=='conflicting_named' and pos==1 and ('onion' not in answer.casefold() or 'different' not in answer.casefold() or route!='retrieve'):problems.append('conflicting named recipe not explained')
  if name=='soup_context' and pos==1 and (not recipe or ingredient_in_record(recipe,'onion') or focus!='Tom yum goong'):problems.append('soup preference not preserved')
  if name=='soup_context' and pos==2 and (focus!='Tom yum goong' or 'Prawns' not in answer):problems.append('lost soup focus')
  row={'scenario':name,'question':q,'answer':answer,'route':route,'focus':focus,'safety':d.get('safety'),'wall_seconds':round(time.perf_counter()-start,2),'problems':problems};rows.append(row);print(name,pos,'PASS' if not problems else 'FAIL '+str(problems),json.dumps({'focus':focus,'answer':answer},ensure_ascii=True),flush=True)
p=root/'results'/f"semantic_context_v1_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json";p.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');print('Saved:',p,flush=True)
if any(r['problems'] for r in rows):raise SystemExit(1)
