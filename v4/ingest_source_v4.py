"""Recreate the versioned UniTools selection from a pinned source file."""
import argparse
import datetime
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCE='https://theunitools.com/data/unitools-recipes-v1.json'
EXCLUDED={'tiramisu','ceviche','spaghetti-carbonara','pesto-alla-genovese'}

def normalize(data):
    selected=[]
    for x in data['recipes']:
        if x['slug'] in EXCLUDED or not x.get('name',{}).get('en') or not x.get('baseServings') or not isinstance(x.get('prepMinutes'),(float,int)) or not isinstance(x.get('cookMinutes'),(float,int)) or not x.get('steps') or len(x.get('ingredients',[]))<3: continue
        if len(selected)==36: break
        ingredients=[]
        for item in x['ingredients']:
            note=item.get('note'); en_note=(note.get('en') if isinstance(note,dict) else note) or ''
            ingredients.append({'name':item['name']['en'],'quantity':item.get('quantity'),'unit':item.get('unit'),'scaling':item.get('scaling'),'note':en_note})
        steps=[]
        for i,step in enumerate(x['steps'],1):
            text=step.get('text',{}).get('en',''); mins=step.get('minutes')
            steps.append(f"{i}. {text}"+(f" [Source step duration: {mins} min]" if mins is not None else ''))
        notes=[f"{i['name']}: {i['note']}" for i in ingredients if i['note']]
        selected.append({'name':x['name']['en'],'slug':x['slug'],'country':x['country'],'servings':x['baseServings'], 'prep_minutes':x['prepMinutes'],'cook_minutes':x['cookMinutes'],'overview':x.get('summary',{}).get('en','')+f" Publisher lists prep {x['prepMinutes']} minutes and cook {x['cookMinutes']} minutes, total {x['prepMinutes']+x['cookMinutes']} minutes. Serves {x['baseServings']}.", 'ingredients':ingredients,'instructions':'\n'.join(steps),'dietary_tags':x.get('diets') or [],'dietary_note':'Source-provided tags only, not verified allergy or dietary safety. Empty tags mean no label supplied; verify ingredients and cross-contact.', 'ingredient_notes':'\n'.join(notes) if notes else 'No ingredient preparation notes are provided in this dataset record.', 'source':'Recipe data: UniTools — theunitools.com, CC BY-SA 4.0 (adapted English fields)', 'source_url':data['landingPage'],'dataset_version':data['version'],'license':'CC BY-SA 4.0'})
    if len(selected)!=36: raise ValueError('Source has fewer than 36 eligible records')
    return selected

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,help='Previously downloaded original source JSON; otherwise download from the official source')
    parser.add_argument('--output',type=Path,required=True,help='New output JSON file; existing files are never overwritten')
    args=parser.parse_args()
    if args.output.exists(): raise SystemExit('Output exists; choose a new file to preserve the previous version.')
    if args.input: raw=args.input.read_bytes()
    else:
        with urllib.request.urlopen(SOURCE,timeout=60) as response: raw=response.read()
    expected=json.loads((ROOT/'data'/'source_manifest_v4.json').read_text(encoding='utf-8'))['source_sha256']
    actual=hashlib.sha256(raw).hexdigest()
    if actual!=expected: raise SystemExit('Source hash changed. Review the new source before creating a new version.')
    recipes=normalize(json.loads(raw))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(recipes,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f'Wrote {len(recipes)} recipes; source SHA-256 {actual}; UTC date {datetime.datetime.now(datetime.timezone.utc).date()}')

if __name__=='__main__': main()
