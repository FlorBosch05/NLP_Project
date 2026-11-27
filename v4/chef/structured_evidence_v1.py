"""Trace the structured recipe fields used to format deterministic answers."""
import json
from chef.conversation_v3 import source_result as vector_source_result


def source_result(index, recipe, text, focus=True):
    result=vector_source_result(index,recipe,text,focus)
    if not result.get('context'):
        return result
    # This is the exact source record used by the formatter, not a similarity hit.
    # Preserve all vector hits and append one clearly labelled structured lookup.
    result['context'].append({
        'text':f"Recipe: {recipe['name']}\ningredients: "+json.dumps(recipe['ingredients'],ensure_ascii=False),
        'metadata':{'recipe':recipe['name'],'section':'ingredients','servings':recipe['servings'],
                    'source':recipe['source'],'source_url':recipe.get('source_url'),
                    'dataset_version':recipe.get('dataset_version'),'license':recipe.get('license'),
                    'evidence_type':'structured_lookup','data_file':'v4/data/recipes_v4.json'},
        'score':None,
    })
    return result
