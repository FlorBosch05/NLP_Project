"""Live interface checks for the readable source panel and unchanged raw trace."""
import json,os,time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ.setdefault('OLLAMA_MODEL','qwen2.5:7b')
from streamlit.testing.v1 import AppTest
from chef.retrieval import read_recipes
ROOT=Path(__file__).resolve().parent

def main():
    rows=[]
    app=AppTest.from_file(str(ROOT/'app_ollama_conversation_v10.py'),default_timeout=600).run()
    for q in ('What are the ingredients for Ratatouille?', 'How many people is that recipe for?'):
        app.chat_input[0].set_value(q).run(timeout=600)
        msgs=app.session_state['messages'];last=msgs[-1];details=last.get('details',{}); problems=[]
        if app.error or app.exception or last.get('role')!='assistant':problems.append('UI error')
        normal=[x for x in app.expander if x.label=='Sources and measurements']
        debug=[x for x in app.expander if x.label=='Debug: complete raw trace']
        if len(normal)!=len(debug) or len(normal)!=sum(m['role']=='assistant' for m in msgs):problems.append('missing panels on current or previous message')
        if not debug or len(debug[-1].json)!=1:problems.append('raw trace unavailable')
        elif json.loads(debug[-1].json[0].value)!=details:problems.append('raw trace changed')
        if normal and normal[-1].json:problems.append('raw JSON leaked into readable panel')
        if normal and not any('UniTools' in x.value for x in normal[-1].markdown):problems.append('missing source link or attribution')
        if q.startswith('What'):
            recipe=next(r for r in read_recipes() if r['name']=='Ratatouille')
            evidence=[c for c in details.get('retrieved_chunks',[]) if c.get('metadata',{}).get('evidence_type')=='structured_lookup']
            if len(evidence)!=1:problems.append('structured evidence missing')
            elif json.loads(evidence[0]['text'].split('\ningredients: ',1)[1])!=recipe['ingredients']:problems.append('raw record changed')
            rendered='\n'.join(str(x.value) for x in normal[-1].text)
            if 'Tomatoes: 600 g' not in rendered or 'Salt and pepper: to taste' not in rendered:problems.append('ingredient display incorrect')
            captions=[x.value for x in normal[-1].caption]
            if 'Stored recipe record' not in captions:problems.append('structured provenance not labelled')
            if 'Search result' in captions and captions.index('Stored recipe record') > captions.index('Search result'):problems.append('record not shown first')
        rows.append({'question':q,'answer':last.get('content'),'problems':problems,'raw_trace':details})
        print(q,'PASS' if not problems else 'FAIL: '+', '.join(problems),flush=True)
    path=ROOT/'results'/f"source_display_final_v1_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
    path.write_text(json.dumps({'app':'app_ollama_conversation_v10.py','cases':rows},indent=2,ensure_ascii=False),encoding='utf-8');print('Saved:',path,flush=True)
    if any(r['problems'] for r in rows):raise SystemExit(1)
if __name__=='__main__':main()
