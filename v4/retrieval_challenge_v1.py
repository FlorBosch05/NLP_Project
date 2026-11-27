"""Ingredient-based retrieval probes without naming the expected recipe."""
import json, os, time
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
from chef.retrieval import build_index

ROOT=Path(__file__).resolve().parent
CASES=[
 ('R01','Which recipe uses kombu, bonito flakes and miso paste?','Miso soup'),
 ('R02','Which recipe uses avocado, lime and jalapeño?','Guacamole'),
 ('R03','Which dish uses rabbit, bomba rice and saffron?','Paella valenciana'),
 ('R04','Which recipe uses beetroot, cabbage and beef?','Borscht'),
 ('R05','Which recipe uses potatoes, eggs and onion to make a thick omelette?','Spanish tortilla'),
 ('R06','Which dish uses toor dal, ghee and turmeric?','Dal tadka'),
]
def main():
    rows=[]
    for strategy in ('sections','recipe'):
        retriever=build_index(strategy).as_retriever(similarity_top_k=5)
        for ident,question,expected in CASES:
            hits=retriever.retrieve(question)
            ranks=[i for i,n in enumerate(hits,1) if n.node.metadata.get('recipe')==expected]
            rows.append({'id':ident,'question':question,'expected_recipe':expected,'strategy':strategy,'rank':ranks[0] if ranks else None,'hits':[{'recipe':n.node.metadata.get('recipe'),'section':n.node.metadata.get('section')} for n in hits]})
            print(strategy,ident,'rank',ranks[0] if ranks else 'miss',flush=True)
    path=ROOT/'results'/f"retrieval_challenge_v1_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
    path.write_text(json.dumps({'note':'Six project-authored ingredient queries, expected recipe in the V4 corpus; target recipe match is not answer quality, Ragas, or independent review.','cases':rows},indent=2,ensure_ascii=False),encoding='utf-8'); print('Saved:',path)
if __name__=='__main__':main()
