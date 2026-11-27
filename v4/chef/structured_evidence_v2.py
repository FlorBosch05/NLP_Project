"""Trace structured recipe ingredients while honoring vector retrieval settings."""
import json


def source_result(index, recipe, text, focus=True, top_k=5):
    query=recipe['name']+' soup recipe ingredients overview'
    nodes=index.as_retriever(similarity_top_k=top_k).retrieve(query)
    chunks=[{'text':n.node.get_content(),'metadata':n.node.metadata,'score':n.score} for n in nodes]
    if not any(c['metadata'].get('recipe')==recipe['name'] for c in chunks):
        return {'route':'retrieve','answer':'I could not retrieve that recipe reliably. Please try another recipe.', 'calls':[], 'recipe_focus':None}
    chunks.append({
        'text':f"Recipe: {recipe['name']}\ningredients: "+json.dumps(recipe['ingredients'],ensure_ascii=False),
        'metadata':{'recipe':recipe['name'],'section':'ingredients','servings':recipe['servings'],
                    'source':recipe['source'],'source_url':recipe.get('source_url'),
                    'dataset_version':recipe.get('dataset_version'),'license':recipe.get('license'),
                    'evidence_type':'structured_lookup','data_file':'v4/data/recipes_v4.json'},
        'score':None,
    })
    return {'route':'retrieve','answer':text,'context':chunks,'search_query':query,
            'calls':[],'ttft_seconds':None,'recipe_focus':recipe['name'] if focus else None}
