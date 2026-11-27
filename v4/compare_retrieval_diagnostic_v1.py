"""Same V4 questions and labels across the two existing chunking strategies."""
import json
import os
import time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
from chef.retrieval import build_index
from check_retrieval_v4 import LABELS

ROOT=Path(__file__).resolve().parent

def main():
    cases=json.loads((ROOT/'data/evaluation_v4.json').read_text(encoding='utf-8'))
    rows=[]
    for strategy in ('sections','recipe'):
        retriever=build_index(strategy).as_retriever(similarity_top_k=5)
        for case in cases:
            if case['id'] not in LABELS: continue
            name,section=LABELS[case['id']]
            start=time.perf_counter(); hits=retriever.retrieve(case['question']); duration=time.perf_counter()-start
            ranks=[i for i,n in enumerate(hits,1) if n.node.metadata.get('recipe')==name and (strategy=='recipe' or n.node.metadata.get('section')==section)]
            rows.append({'strategy':strategy,'id':case['id'],'expected_recipe':name,'expected_section':section,
                         'rank':ranks[0] if ranks else None,'context_characters':sum(len(n.node.get_content()) for n in hits),
                         'retrieval_seconds':round(duration,5),'hits':[{'recipe':n.node.metadata.get('recipe'),'section':n.node.metadata.get('section'),'score':n.score} for n in hits]})
            print(strategy,case['id'],'rank',ranks[0] if ranks else 'miss',flush=True)
    result={'note':'13 project-labelled, mostly named-recipe cases. Recipe chunks contain all sections; characters are a context-size proxy, not model tokens. Single-run timing, not Ragas or independent reference verification.','top_k':5,'cases':rows}
    path=ROOT/'results'/f"retrieval_comparison_v4_v1_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
    path.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8'); print('Saved:',path,flush=True)

if __name__=='__main__': main()
