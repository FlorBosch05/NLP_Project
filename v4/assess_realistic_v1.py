"""Check selected observable outcomes of a saved realistic-conversation run."""
import argparse,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args()
 d=json.loads(a.run.read_text(encoding='utf-8'));rows=d['turns']; recipes={r['name']:r for r in json.loads((ROOT/'data/recipes_v4.json').read_text(encoding='utf-8'))}
 grouped={}
 for row in rows:grouped.setdefault(row['scenario'],[]).append(row)
 checks=[]
 def check(name,condition): checks.append({'check':name,'pass':bool(condition)});print(name,'PASS' if condition else 'FAIL')
 def focused(row,name):return row.get('route')=='retrieve' and row.get('focus')==name and name in row.get('context_recipes',[])
 for scenario,n in [('vegetarian',4),('alternative',3),('switch',3),('gazpacho',3),('preferences',2),('ambiguous',2),('safety',2)]:check(scenario+'_complete',len(grouped.get(scenario,[]))==n and all(not x.get('errors') and not x.get('exceptions') and not x.get('error') for x in grouped.get(scenario,[])))
 try:
  v=grouped['vegetarian'];name=v[0]['focus']; check('vegetarian_source_tag',focused(v[0],name) and 'vegetarian' in recipes[name]['dietary_tags']);check('vegetarian_focus_and_ingredients',focused(v[1],name) and all(i['name'] in v[1]['answer'] for i in recipes[name]['ingredients']));check('vegetarian_servings',focused(v[2],name) and str(recipes[name]['servings']) in v[2]['answer']);check('vegetarian_doubled',v[3]['route']=='scale' and v[3].get('mcp_call',{}).get('arguments',{}).get('to_servings')==8)
  t=grouped['alternative']; name=t[1]['focus'];check('different_onion_free',focused(t[1],name) and name!=t[0]['focus'] and all('onion' not in i['name'].casefold() for i in recipes[name]['ingredients']));check('different_focus_retained',focused(t[2],name))
  s=grouped['switch'];check('recipe_switch_to_borscht',focused(s[1],'Borscht') and focused(s[2],'Borscht') and '6' in s[2]['answer'])
  g=grouped['gazpacho'];check('tomato_soup_cold',focused(g[0],'Gazpacho') and 'cold' in g[0]['answer'].lower());check('gazpacho_ingredients',focused(g[1],'Gazpacho') and all(i['name'] in g[1]['answer'] for i in recipes['Gazpacho']['ingredients']));check('gazpacho_eight',g[2]['route']=='scale' and g[2].get('mcp_call',{}).get('arguments',{}).get('to_servings')==8)
  x=grouped['preferences'];name=x[0]['focus'];check('meatless_source_vegan',focused(x[0],name) and 'vegan' in recipes[name]['dietary_tags']);check('stock_answer_is_grounded',focused(x[1],name) and ('beef stock' in x[1]['answer'].lower()) and not any('beef stock' in i['name'].lower() for i in recipes[name]['ingredients']))
  check('ambiguous_requests_clarify',all('Which recipe' in r.get('answer','') for r in grouped['ambiguous']));check('allergy_blocks',all(r.get('route')=='safety_block' for r in grouped['safety']))
 except (KeyError,IndexError,TypeError) as exc:check('assessment_incomplete_'+type(exc).__name__,False)
 path=ROOT/'results'/f"realistic_assessment_v1_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json";path.write_text(json.dumps({'source_run':str(a.run),'checks':checks},indent=2),encoding='utf-8');print('Saved:',path)
 if any(not c['pass'] for c in checks):raise SystemExit(1)
if __name__=='__main__':main()
