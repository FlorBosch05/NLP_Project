"""Offline smoke tests: run from NLPproject with python v2/test_mvp.py."""
import asyncio
import json
from pathlib import Path
from chef.agent import invoke_mcp
from chef.retrieval import make_documents, read_recipes

async def test_tools():
    converted = await invoke_mcp('convert_units', {'amount': 2, 'from_unit':'kilograms', 'to_unit':'grams'})
    assert converted == {'amount':2000, 'unit':'g'}
    scaled = await invoke_mcp('scale_recipe', {'ingredients':[{'name':'tomato','quantity':200,'unit':'g'}], 'from_servings':2, 'to_servings':5})
    assert scaled['result'][0]['quantity'] == 500
    try:
        await invoke_mcp('convert_units', {'amount':1, 'from_unit':'g', 'to_unit':'ml'})
    except ValueError as error:
        assert 'density' in str(error)
    else:
        raise AssertionError('Mass-to-volume conversion should be rejected')

def main():
    recipes = read_recipes()
    assert len(recipes) == 30 and len({r['name'] for r in recipes}) == 30
    assert len(make_documents('sections')) == 120
    assert len(make_documents('recipe')) == 30
    cases = json.loads((Path(__file__).parent / 'data' / 'evaluation_v2.json').read_text(encoding='utf-8'))
    assert len(cases) == 20
    asyncio.run(test_tools())
    print('Dataset, chunking and MCP smoke tests passed.')

if __name__ == '__main__': main()
