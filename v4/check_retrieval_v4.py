"""Check whether labelled evidence appears in top five retrieved chunks."""
import json
import time
from pathlib import Path
from chef.retrieval import build_index

ROOT=Path(__file__).resolve().parent
LABELS={
    'Q01':('Ratatouille','ingredients'), 'Q02':('Guacamole','ingredients'),
    'Q03':('Miso soup','ingredients'), 'Q04':('Dal tadka','ingredients'),
    'Q05':('Borscht','ingredients'), 'Q06':('Ratatouille','dietary'),
    'Q07':('Guacamole','dietary'), 'Q08':('Miso soup','dietary'),
    'Q09':('Ratatouille','overview'), 'Q10':('Miso soup','overview'),
    'Q11':('Borscht','overview'), 'Q12':('Spanish tortilla','instructions'),
    'Q13':('Paella valenciana','ingredient_notes'),
}

def main():
    cases=json.loads((ROOT/'data'/'evaluation_v4.json').read_text(encoding='utf-8'))
    index=build_index('sections'); retriever=index.as_retriever(similarity_top_k=5)
    rows=[]
    for c in cases:
        if c['id'] not in LABELS: continue
        name,section=LABELS[c['id']]
        hits=retriever.retrieve(c['question'])
        ranks=[i for i,n in enumerate(hits,1) if n.node.metadata.get('recipe')==name and n.node.metadata.get('section')==section]
        rows.append({'id':c['id'],'question':c['question'],'expected_recipe':name,'expected_section':section,'rank':ranks[0] if ranks else None,'retrieved':[{'recipe':n.node.metadata.get('recipe'),'section':n.node.metadata.get('section'),'score':n.score} for n in hits]})
    out=ROOT/'results'/f"retrieval_check_v4_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
    out.write_text(json.dumps({'top_k':5,'note':'AI-authored labels and mostly named-recipe questions; this is not Ragas or independent verification.','cases':rows},indent=2,ensure_ascii=False),encoding='utf-8')
    print('Evidence in top five:',sum(x['rank'] is not None for x in rows),'/',len(rows))
    print('Evidence ranked first:',sum(x['rank']==1 for x in rows),'/',len(rows))
    print('Saved:',out)

if __name__=='__main__': main()
