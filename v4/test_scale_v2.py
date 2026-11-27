"""Offline checks for sourced recipes, retrieval data and the MCP server."""
import asyncio
import json
import math
from pathlib import Path
from chef.agent_scale_v2 import invoke_mcp, create_graph, Decision, QwenScaleArguments
from chef.retrieval import read_recipes, make_documents

ROOT=Path(__file__).resolve().parent

async def verify_tools():
    items=[{'name':'rice','quantity':200,'unit':'g','scaling':'linear'}, {'name':'pepper','quantity':1,'unit':'tsp','scaling':'damped'}, {'name':'water','quantity':100,'unit':'ml','scaling':'fixed'}, {'name':'salt','quantity':None,'unit':'toTaste','scaling':'fixed'}]
    result=await invoke_mcp('scale_recipe',{'ingredients':items,'from_servings':2,'to_servings':4})
    values=result['result']
    assert values[0]['quantity']==400 and values[0]['status']=='linear'
    assert values[1]['quantity'] is None and values[1]['original_quantity']==1 and 'adjust manually' in values[1]['status']
    assert values[2]['quantity']==100 and values[2]['status']=='fixed'
    assert values[3]['quantity'] is None and 'No numeric source quantity' in values[3]['status']
    converted=await invoke_mcp('convert_units',{'amount':2,'from_unit':'kg','to_unit':'g'})
    assert converted=={'amount':2000,'unit':'g'}
    try: await invoke_mcp('convert_units',{'amount':1,'from_unit':'g','to_unit':'ml'})
    except ValueError as e: assert 'density' in str(e)
    else: raise AssertionError('Mass-to-volume conversion without density was accepted')

def verify_graph(cases):
    class Raw:
        usage_metadata={'input_tokens':1,'output_tokens':1}
    class Chunk:
        content='Test response.'
        usage_metadata={'input_tokens':1,'output_tokens':1}
    class FakeModel:
        def with_structured_output(self,schema,**kwargs):
            self.schema=schema
            return self
        def invoke(self,messages):
            parsed=Decision(route='scale',search_query='Ratatouille') if self.schema is Decision else QwenScaleArguments(to_servings=8)
            return {'parsed':parsed,'raw':Raw()}
        def stream(self,messages):
            yield Chunk()
    class FakeIndex:
        def as_retriever(self,**kwargs): return self
        def retrieve(self,question): return []
    result=create_graph(FakeIndex(),model=FakeModel()).invoke({'question':'Scale Ratatouille from 4 to 8 servings.','history':[]})
    expected=next(c['expected_tool_result'] for c in cases if c['id']=='Q18')
    assert result['route']=='scale' and json.loads(result['tool_result'])==expected
    assert '1200 g' in result['answer'] and 'adjust manually' in result['answer']
    assert 'Source cooking steps' in result['answer'] and 'Fry the aubergine' not in result['answer']

def main():
    recipes=read_recipes()
    manifest=json.loads((ROOT/'data'/'source_manifest_v4.json').read_text(encoding='utf-8'))
    cases=json.loads((ROOT/'data'/'evaluation_v4.json').read_text(encoding='utf-8'))
    assert len(recipes)==36 and len(cases)==20
    assert [x['slug'] for x in recipes]==manifest['recipe_slugs']
    assert len({x['slug'] for x in recipes})==36 and len({x['name'] for x in recipes})==36
    assert len(make_documents('sections'))==180 and len(make_documents('recipe'))==36
    for recipe in recipes:
        assert recipe['servings']>0 and recipe['instructions'] and recipe['license']=='CC BY-SA 4.0'
        assert recipe['prep_minutes']>=0 and recipe['cook_minutes']>=0 and recipe['ingredients']
        for i in recipe['ingredients']:
            assert i['name'] and i['unit'] and i['scaling'] in {'linear','damped','fixed'}
            assert i['quantity'] is None or isinstance(i['quantity'],(float,int)) and math.isfinite(i['quantity']) and i['quantity']>=0
    asyncio.run(verify_tools())
    verify_graph(cases)
    print('Source structure and real MCP tool checks passed; recipe content and tags are not independently verified.')

if __name__=='__main__': main()
