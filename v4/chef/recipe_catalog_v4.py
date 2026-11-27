"""Structured catalogue queries and reviewed recipe views for the conversation.

Only tightly bounded request forms trigger these read-only paths. Other requests
continue to the normal model-based safety and conversation workflow.
"""
import json
import re
from chef.ingredient_selection_v4 import canonical, STEPS
from chef.retrieval import read_recipes
from chef.conversation_v8 import listing
from chef.conversation_shortcuts_v2 import REVIEWED_STEPS
TORTILLA_ANSWER = 'Gently cook potatoes and onions in olive oil, drain, then combine with beaten eggs. Cook in a pan, flip and cook until the centre reaches 71°C (160°F), measured with a food thermometer. Recipe adapted from UniTools, CC BY-SA 4.0. The temperature check is a food-safety adaptation based on FoodSafety.gov.'

BIBIMBAP_STEPS = (
    '1. Marinate the beef with soy sauce, garlic and a little sesame oil in the refrigerator for 20 minutes.\n'
    '2. Blanch the spinach and squeeze it dry. Boil the soybean sprouts for 3 minutes. Dress the vegetables with sesame oil; add garlic to the sprouts.\n'
    '3. Fry the carrot and mushrooms separately and season them.\n'
    '4. Cook the beef strips to at least 63°C (145°F), measured with a food thermometer, and allow a 3-minute rest. Fry the eggs separately until both whites and yolks are firm. Use clean utensils and plates for cooked food.\n'
    '5. Divide the hot rice between bowls, arrange the vegetables and beef on top, add an egg and gochujang, and mix before eating.\n\n'
    'The beef and egg safety steps adapt the source instructions. [FDA safe food handling guidance](https://www.fda.gov/food/buy-store-serve-safe-food/safe-food-handling).'
)

def list_request(question):
    q=re.sub(r'[.!?]+$', '', question.casefold().strip())
    patterns=[
        r'(?:do you have |are there |show me )?(?:any |some |the )?(?:other |more |different |another )?recipes? (?:with|containing|using) ([a-z]+)',
        r'(?:i want |show me |give me )?(?:a |the )?list of ([a-z]+) (?:having|containing) recipes',
        r'(?:list|show me|give me) (?:all |some |the )?recipes? (?:with|containing|using) ([a-z]+)',
        r'(?:which|what) recipes? (?:have|contain|use) ([a-z]+)',
    ]
    for pattern in patterns:
        match=re.fullmatch(pattern,q)
        if match: return canonical(match.group(1)), bool(re.search(r'\b(?:other|different|more|another)\b',q))
    return None

def named_request(question,recipes):
    q=re.sub(r'[.!?]+$', '', question.casefold().strip())
    name=q
    patterns=[r'(?:ok(?:ay)?\s+)?(?:please\s+)?(?:give|show) me (?:a |the )?recipe for (.+?)(?: please)?',
              r'(?:please\s+)?(?:give|show) me (?:a |the )?(.+?) recipe(?: please)?',
              r'(?:i (?:choose|want)|give me|show me) (?:the )?(.+?)(?: please)?']
    for pattern in patterns:
        m=re.fullmatch(pattern,q)
        if m:
            name=m.group(1).strip();break
    return next((r for r in recipes if r['name'].casefold()==name),None)

def record(recipe,section='ingredients'):
    body=json.dumps(recipe['ingredients'],ensure_ascii=False) if section=='ingredients' else recipe['instructions']
    return {'text':f"Recipe: {recipe['name']}\n{section}: {body}",
            'metadata':{'recipe':recipe['name'],'section':section,'servings':recipe['servings'],
                        'source':recipe['source'],'source_url':recipe.get('source_url'),
                        'dataset_version':recipe.get('dataset_version'),'license':recipe.get('license'),
                        'evidence_type':'structured_lookup','data_file':'v4/data/recipes_v4.json'},'score':None}

def known_ingredients(recipes):
    return {canonical(w) for r in recipes for ingredient in r['ingredients'] for w in re.findall(r'[a-z]+',ingredient['name'].casefold()) if len(w)>2}

def ingredient_in_record(recipe,token):
    """Match ingredient-name words, including e.g. tomato paste, not eggplant."""
    return any(token in [canonical(w) for w in re.findall(r'[a-z]+',item['name'].casefold())] for item in recipe['ingredients'])

class RecipeCatalogGraph:
    def __init__(self,inner): self.inner=inner
    def invoke(self,state):
        question=state['question']; history=state.get('history',[]); recipes=read_recipes()
        request=list_request(question); named=named_request(question,recipes)
        if request and request[0] not in known_ingredients(recipes): request=None
        if not request and not named: return self.inner.invoke(state)
        # No free-form user text enters these answers: exact request grammars,
        # known ingredient/name and source-backed fixed templates are required.
        if request:
            token,other=request
            matches=[r for r in recipes if ingredient_in_record(r,token)]
            if other:
                shown=' '.join(str(m.get('content','')).casefold() for m in history if m.get('role')=='assistant')
                matches=[r for r in matches if r['name']!=state.get('recipe_focus') and r['name'].casefold() not in shown]
            if not matches:
                return {'route':'retrieve','answer':f'I could not find another matching recipe in the collection.' if other else f'I could not find a recipe with {token} in the collection.', 'calls':[], 'safety':{'stage':'structured_catalogue','category':'allow'}}
            text=f"Recipes whose recorded ingredients include {token}:\n\n"+'\n'.join(f"- {r['name']} (serves {r['servings']})" for r in matches)
            text+='\n\nWhich one would you like?'
            return {'route':'retrieve','answer':text,'context':[record(r) for r in matches],'search_query':f'structured ingredient lookup: {token}','recipe_focus':None,'calls':[], 'safety':{'stage':'structured_catalogue','category':'allow'}}
        recipe=named
        text=listing(recipe)
        context=[record(recipe)]
        reviewed={'Bibimbap':BIBIMBAP_STEPS,**REVIEWED_STEPS,**STEPS,'Spanish tortilla':TORTILLA_ANSWER}
        if recipe['name'] in reviewed:
            text+='\n\nPreparation (adapted from the source):\n'+reviewed[recipe['name']]
            context.append(record(recipe,'instructions'))
        else:
            text+='\n\nI can show the ingredients, but I cannot yet provide reviewed preparation steps for this recipe.'
        return {'route':'retrieve','answer':text,'context':context,'search_query':f"structured recipe lookup: {recipe['name']}", 'recipe_focus':recipe['name'],'calls':[], 'safety':{'stage':'structured_catalogue','category':'allow'}}
