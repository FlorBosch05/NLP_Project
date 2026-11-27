"""Check corpus structure and evaluation references without Groq or network."""
import json
import math
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def run_audit():
    recipes=json.loads((ROOT/'data'/'recipes_v3.json').read_text(encoding='utf-8'))
    cases=json.loads((ROOT/'data'/'evaluation_v3.json').read_text(encoding='utf-8'))
    errors=[]
    names=set()
    for r in recipes:
        name=r.get('name','')
        if not name or name in names: errors.append(f'Invalid or duplicate name: {name}')
        names.add(name)
        if not r.get('instructions') or not r.get('substitutions') or not r.get('dietary_note'): errors.append(f'{name}: missing instructions or notes')
        if not isinstance(r.get('servings'),int) or r['servings']<=0: errors.append(f'{name}: invalid servings')
        if not isinstance(r.get('cooking_time_minutes_estimate'),(int,float)) or r['cooking_time_minutes_estimate']<=0: errors.append(f'{name}: invalid estimated time')
        if not r.get('ingredients'): errors.append(f'{name}: no ingredients')
        for item in r.get('ingredients',[]):
            q=item.get('quantity')
            if not item.get('name') or not item.get('unit') or not isinstance(q,(int,float)) or not math.isfinite(q) or q<=0: errors.append(f'{name}: invalid ingredient {item}')
        if not r.get('dietary_tags') or not set(r['dietary_tags']).issubset({'vegan','vegetarian','contains meat','contains fish'}): errors.append(f'{name}: invalid tags')
    if len(recipes)!=30 or len(cases)!=20: errors.append('Expected 30 recipes and 20 cases')
    by_name={r['name']:r for r in recipes}; by_id={c['id']:c for c in cases}
    if len(by_id)!=20: errors.append('Duplicate evaluation IDs')
    checks={
        'Q01': all(x in by_id['Q01']['reference'] for x in ['200 g pasta','300 g tomatoes','15 ml olive oil']) and [i['quantity'] for i in by_name['Tomato pasta']['ingredients']]==[200,300,15],
        'Q02': [i['quantity'] for i in by_name['Mushroom pasta']['ingredients']]==[200,250,15] and all(x in by_id['Q02']['reference'] for x in ['200 g pasta','250 g mushrooms','15 ml olive oil']),
        'Q03': 'lentils' in by_id['Q03']['reference'] and 'carrots' in by_id['Q03']['reference'] and 'tender' in by_name['Lentil soup']['instructions'],
        'Q04': [i['quantity'] for i in by_name['Chickpea salad']['ingredients']]==[240,150,150] and all(x in by_id['Q04']['reference'] for x in ['240 g chickpeas','150 g cucumber','150 g tomatoes']),
        'Q05': [i['quantity'] for i in by_name['Carrot soup']['ingredients']]==[400,100,500] and all(x in by_id['Q05']['reference'] for x in ['400 g carrots','100 g onion','500 ml water']),
        'Q06': by_name['Tofu stir fry']['servings']==2 and 'two' in by_id['Q06']['reference'],
        'Q07': by_name['Baked potatoes']['cooking_time_minutes_estimate']==45 and '45 minutes' in by_id['Q07']['reference'],
        'Q08': 'peas and onion' in by_name['Pea soup']['instructions'].lower() and 'peas and onion' in by_id['Q08']['reference'].lower(),
        'Q09': [i['quantity'] for i in by_name['Chicken rice bowl']['ingredients']]==[250,150,150] and all(x in by_id['Q09']['reference'] for x in ['250 g chicken breast','150 g rice','150 g carrots']),
        'Q10': 'vegan' in by_name['Lentil soup']['dietary_tags'] and 'vegan' in by_id['Q10']['reference'].lower(),
        'Q11': 'white beans' in by_name['Chickpea salad']['substitutions'] and 'white beans' in by_id['Q11']['reference'],
        'Q12': 'another pasta' in by_name['Tomato pasta']['substitutions'] and 'another pasta' in by_id['Q12']['reference'],
        'Q13': 'plant-based drink' in by_name['Oat porridge']['substitutions'] and 'plant-based drink' in by_id['Q13']['reference'],
    }
    for case,ok in checks.items():
        if not ok: errors.append(f'{case}: reference consistency check failed')
    numeric={'Q14':(2000,'g'),'Q15':(.5,'l'),'Q16':(45,'ml'),'Q17':(.25,'kg')}
    for case,(amount,unit) in numeric.items():
        expected=by_id[case].get('expected_tool_result',{})
        if expected.get('amount')!=amount or expected.get('unit')!=unit: errors.append(f'{case}: conversion reference mismatch')
    for case,name,multiplier in [('Q18','Tomato pasta',2.5),('Q19','Mushroom pasta',2)]:
        calculated=[{**i,'quantity':i['quantity']*multiplier} for i in by_name[name]['ingredients']]
        if by_id[case].get('expected_tool_result',{}).get('result')!=calculated: errors.append(f'{case}: scaled reference mismatch')
    for name in ('Chicken rice bowl','Chicken tomato skillet'):
        if '74°C' not in by_name[name]['instructions']: errors.append(f'{name}: missing poultry temperature')
    if '63°C' not in by_name['Salmon rice bowl']['instructions']: errors.append('Salmon rice bowl: missing fish temperature')
    for name in ('Potato omelette','Vegetable omelette','Egg fried rice'):
        if '71°C' not in by_name[name]['instructions']: errors.append(f'{name}: missing egg-dish temperature')
    for name in ('Chickpea salad','Bean salad','Sweet potato beans','Chickpea curry','White bean tomato stew'):
        if 'canned or fully cooked' not in by_name[name]['instructions'].lower(): errors.append(f'{name}: unclear pulse preparation')
    return {'recipe_count':len(recipes),'evaluation_count':len(cases),'reference_checks':checks,'errors':errors,'limitations':['Automated consistency checks do not validate taste, cooking time, dietary safety, substitutions, completeness of all instructions or human ground truth.','Q20 is a greeting without a single exact ground-truth response.','Temperatures follow the cited FoodSafety.gov chart; local guidance may differ.']}

if __name__=='__main__':
    result=run_audit()
    output=ROOT/'results'/f"data_audit_v3_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns()%1000000:06d}.json"
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(result,indent=2,ensure_ascii=False))
    if result['errors']: raise SystemExit(1)
