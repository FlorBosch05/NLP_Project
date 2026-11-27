"""Compare section and complete-recipe retrieval on fixed v3 queries."""
import json
import time
from pathlib import Path
import os
from transformers import AutoTokenizer
from chef.retrieval import build_index

ROOT=Path(__file__).resolve().parent
LABELS={
    'Q01':('Tomato pasta','ingredients'), 'Q02':('Mushroom pasta','ingredients'),
    'Q03':('Lentil soup','instructions'), 'Q04':('Chickpea salad','ingredients'),
    'Q05':('Carrot soup','ingredients'), 'Q06':('Tofu stir fry','overview'),
    'Q07':('Baked potatoes','overview'), 'Q08':('Pea soup','instructions'),
    'Q09':('Chicken rice bowl','ingredients'), 'Q10':('Lentil soup','dietary'),
    'Q11':('Chickpea salad','substitutions'), 'Q12':('Tomato pasta','substitutions'),
    'Q13':('Oat porridge','substitutions'),
}

def main():
    cases=json.loads((ROOT/'data'/'evaluation_v3.json').read_text(encoding='utf-8'))
    cases=[c for c in cases if c['id'] in LABELS]
    encoder=AutoTokenizer.from_pretrained(os.getenv('EMBEDDING_MODEL','sentence-transformers/all-MiniLM-L6-v2'),cache_dir=str(ROOT.parent/'storage'/'models'))
    rows=[]
    for strategy in ('sections','recipe'):
        index=build_index(strategy)
        retriever=index.as_retriever(similarity_top_k=5)
        for case in cases:
            start=time.perf_counter()
            hits=retriever.retrieve(case['question'])
            elapsed=time.perf_counter()-start
            recipe,section=LABELS[case['id']]
            recipe_hit=any(n.node.metadata.get('recipe')==recipe for n in hits)
            evidence_hit=any(n.node.metadata.get('recipe')==recipe and (strategy=='recipe' or n.node.metadata.get('section')==section) for n in hits)
            texts=[n.node.get_content() for n in hits]
            rows.append({'strategy':strategy,'id':case['id'],'question':case['question'],'target_recipe':recipe,'target_section':section,'recipe_hit':recipe_hit,'labeled_evidence_hit':evidence_hit,'context_tokens_embedding_tokenizer_estimate':sum(len(encoder.encode(t,add_special_tokens=False)) for t in texts),'retrieval_seconds':round(elapsed,4),'chunks':[{'text':n.node.get_content(),'metadata':n.node.metadata,'score':n.score} for n in hits]})
            print(strategy,case['id'],'evidence',evidence_hit,flush=True)
    destination=ROOT/'results'/f"retrieval_comparison_{time.strftime('%Y%m%d_%H%M%S')}.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps({'top_k':5,'note':'13 AI-labelled cases, named-recipe questions; tokens use the embedding tokenizer as an estimate, not the Groq tokenizer or billing. Not Ragas. No independent human audit.','rows':rows},indent=2,ensure_ascii=False),encoding='utf-8')
    print('Saved:',destination)

if __name__=='__main__': main()
