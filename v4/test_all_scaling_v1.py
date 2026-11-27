"""Validate the real MCP scaling tool against all sourced V4 recipes offline."""
import asyncio
import json
import math
import sys
import time
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from chef.retrieval import read_recipes

ROOT=Path(__file__).resolve().parent

async def check():
    params=StdioServerParameters(command=sys.executable,args=['-m','chef.mcp_server'],cwd=str(ROOT))
    reports=[]
    async with stdio_client(params) as (reader,writer):
        async with ClientSession(reader,writer) as session:
            await session.initialize()
            for recipe in read_recipes():
                errors=[]
                result=await session.call_tool('scale_recipe',arguments={'ingredients':recipe['ingredients'],'from_servings':recipe['servings'],'to_servings':recipe['servings']*2})
                items=(result.structuredContent or {}).get('result',[])
                if result.isError or len(items)!=len(recipe['ingredients']): errors.append('tool error or ingredient count mismatch')
                for source,actual in zip(recipe['ingredients'],items):
                    if actual.get('name')!=source['name'] or actual.get('unit')!=source['unit']: errors.append('ingredient identity mismatch')
                    value,rule=source['quantity'],source['scaling']
                    if value is None or rule=='damped':
                        if actual.get('quantity') is not None: errors.append('unsupported quantity invented: '+source['name'])
                        expected_status='No numeric source quantity' if value is None else 'adjust manually'
                        if expected_status not in actual.get('status',''): errors.append('missing manual adjustment warning: '+source['name'])
                    else:
                        expected=round(value*2,3) if rule=='linear' else value
                        if not math.isclose(actual.get('quantity',float('nan')),expected,rel_tol=1e-9,abs_tol=1e-9): errors.append('wrong scaled quantity: '+source['name'])
                        if actual.get('status')!=rule: errors.append('wrong scaling status: '+source['name'])
                reports.append({'recipe':recipe['name'],'errors':errors})
    return reports

def main():
    results=asyncio.run(check())
    path=ROOT/'results'/f"scaling_all_recipes_v1_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
    path.write_text(json.dumps({'factor':2,'test':'Real local MCP tool, no LLM; compares each output with stored source scaling rule','recipes':results},indent=2,ensure_ascii=False),encoding='utf-8')
    failures=[r for r in results if r['errors']]
    print('Recipes passed:',len(results)-len(failures),'/',len(results));print('Saved:',path)
    if failures:
        for row in failures: print(row)
        raise SystemExit(1)

if __name__=='__main__': main()
