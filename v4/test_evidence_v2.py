"""Check structured evidence fidelity for all recipes and live UI examples."""
import json,os,time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
from streamlit.testing.v1 import AppTest
from chef.structured_evidence_v1 import source_result
from chef.retrieval import read_recipes
ROOT=Path(__file__).resolve().parent
os.environ['HF_HUB_OFFLINE']='1';os.environ.setdefault('OLLAMA_MODEL','qwen2.5:7b')

class Node:
    def __init__(self,name):self.metadata={'recipe':name,'section':'overview'}
    def get_content(self):return 'test vector hit'
class Hit:
    def __init__(self,name):self.node=Node(name);self.score=0.7
class Index:
    def __init__(self,name):self.name=name
    def as_retriever(self,**kwargs):return self
    def retrieve(self,query):return [Hit(self.name)]

def verify(recipe,contexts):
    problems=[]; evidence=[x for x in contexts if x.get('metadata',{}).get('evidence_type')=='structured_lookup']
    if len(evidence)!=1:return ['expected exactly one structured record']
    e=evidence[0];metadata=e['metadata'];prefix=f"Recipe: {recipe['name']}\ningredients: "
    if not e['text'].startswith(prefix):problems.append('incorrect ingredient record header')
    else:
        try:
            if json.loads(e['text'][len(prefix):])!=recipe['ingredients']:problems.append('record differs from stored ingredients')
        except ValueError:problems.append('invalid ingredient JSON')
    if e.get('score') is not None or metadata.get('section')!='ingredients' or metadata.get('recipe')!=recipe['name'] or metadata.get('data_file')!='v4/data/recipes_v4.json':problems.append('incorrect provenance')
    return problems

def main():
    rows=[];recipes=read_recipes()
    for recipe in recipes:
        result=source_result(Index(recipe['name']),recipe,'example')
        problems=verify(recipe,result.get('context',[]))
        if len(result.get('context',[]))!=2 or result['context'][0]['score']!=0.7:problems.append('vector hit not preserved')
        rows.append({'kind':'record','recipe':recipe['name'],'problems':problems})
    for name in ('Ratatouille','Dal tadka','Borscht'):
        recipe=next(r for r in recipes if r['name']==name)
        try:
            app=AppTest.from_file(str(ROOT/'app_ollama_conversation_v8.py'),default_timeout=600).run()
            app.chat_input[0].set_value(f'What are the ingredients for {name}?').run(timeout=600)
            last=app.session_state['messages'][-1];details=last.get('details',{});contexts=details.get('retrieved_chunks') or []
            problems=verify(recipe,contexts)
            if app.error or app.exception or details.get('route')!='retrieve':problems.append('UI or routing error')
            if any(i['name'] not in last.get('content','') for i in recipe['ingredients']):problems.append('ingredient missing from answer')
            rows.append({'kind':'live_ui','recipe':name,'problems':problems,'context_count':len(contexts),'answer':last.get('content')})
        except Exception as exc:rows.append({'kind':'live_ui','recipe':name,'problems':[f'{type(exc).__name__}: {exc}']})
        print(name,'PASS' if not rows[-1]['problems'] else 'FAIL: '+', '.join(rows[-1]['problems']),flush=True)
    path=ROOT/'results'/f"evidence_tests_v2_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
    path.write_text(json.dumps({'app':'app_ollama_conversation_v8.py','cases':rows},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Records passed:',sum(not x['problems'] for x in rows if x['kind']=='record'),'/',len(recipes));print('Saved:',path,flush=True)
    if any(x['problems'] for x in rows):raise SystemExit(1)
if __name__=='__main__':main()
