"""Project-specific food-safety actions run by NeMo Colang rails."""
import re
from difflib import SequenceMatcher
from nemoguardrails.actions import action

ALLERGY=re.compile(r'\b(?:allerg(?:y|ies|ic|en|ens)|anaphylaxis|coeliac|celiac|allergie|allergisch|anafylaxie)\b',re.I)
HAZARD=re.compile(r'\b(?:bleach|ammonia|antifreeze|detergent|rat poison|pesticide|methanol|arsenic|cyanide|bleekmiddel|bleekwater|ammoniak|antivries|schoonmaakmiddel|rattengif|bestrijdingsmiddel|arseen)\b',re.I)
INJECTION=re.compile(r'\b(?:ignore|disregard|forget|override|negeer|vergeet|omzeil)\b.{0,100}\b(?:instructions?|rules?|safety|system|policy|instructies?|regels?|veiligheid)\b|\b(?:jailbreak|developer mode|system prompt|systeemprompt)\b',re.I|re.S)
UNSAFE_ASSURANCE=re.compile(r'\b(?:guaranteed|definitely|completely|100\s*%|absolutely)\s+(?:allergen[- ]free|safe for (?:any|all|everyone)|safe for (?:your|an?|the) allerg(?:y|ies))\b',re.I)
EGG=re.compile(r'\b(?:eggs?|egg yolks?|yolks?|eieren?|eigeel|eidooier)\b',re.I)
PREPARATION=re.compile(r'\b(?:cook|cooked|cooking|fry|frying|fried|heat|bake|baked|stir|mix|whisk|beat|break|crack|raw|runny|loose|soft|set|serve|prepar(?:e|ation)|instructions?|kook|bak|rauw|zacht|gaar)\b',re.I)
UNSAFE_EGG=re.compile(r'\b(?:runny|loose|raw|undercooked|rauw|vloeibaar)\b',re.I)

def approved_egg_answer(answer):
    """Exact reviewed templates only; never trust an answer's own safety label."""
    from chef.retrieval import read_recipes
    from chef.conversation_v8 import listing
    from chef.ingredient_selection_v2 import STEPS, canonical
    from chef.recipe_catalog_v2 import BIBIMBAP_STEPS,TORTILLA_ANSWER
    recipes={r['name']:r for r in read_recipes()}
    allowed={TORTILLA_ANSWER}
    for name,steps in [('Menemen',STEPS['Menemen']),('Bibimbap',BIBIMBAP_STEPS),('Spanish tortilla',TORTILLA_ANSWER)]:
        r=recipes[name]; base=listing(r)+'\n\nPreparation (adapted from the source):\n'+steps
        allowed.add(base)
        if name=='Menemen':
            words={canonical(w) for i in r['ingredients'] for w in re.findall(r'[a-z]+',i['name'].casefold())}
            for word in words: allowed.add(f'{name} contains {word}.\n\n'+base)
    return answer in allowed

def hazardous(text):
    words=re.findall(r'[a-z]+',str(text).casefold())
    return bool(HAZARD.search(str(text)) or any(len(w)>=6 and SequenceMatcher(None,w,'cyanide').ratio()>=.70 for w in words))

def standalone_unit_conversion(question):
    """Recognize a numeric, ingredient-free conversion within a unit family."""
    q=question.strip().casefold()
    match=re.fullmatch(r'(?:okay,?\s*)?(?:(?:unrelated question|on a different topic):\s*)?(?:what is|how much is|convert)\s+\d+(?:[.,]\d+)?\s+([a-z]+)\s+(?:in|to)\s+([a-z]+)[.!?]*',q)
    if not match:return False
    mass={'g','gram','grams','kg','kilogram','kilograms','lb','lbs','pound','pounds','oz','ounce','ounces'}
    volume={'ml','milliliter','milliliters','l','liter','liters','tsp','teaspoon','teaspoons','tbsp','tablespoon','tablespoons','cup','cups'}
    first,second=match.groups()
    return (first in mass and second in mass) or (first in volume and second in volume)

def input_category(q,history):
    if INJECTION.search(q): return 'injection'
    if hazardous(q): return 'hazard'
    if ALLERGY.search(q): return 'allergy'
    # A complete, food-free numerical conversion does not depend on the allergy.
    # Other messages retain the earlier allergy context and remain conservative.
    if standalone_unit_conversion(q): return None
    if any(ALLERGY.search(str(m.get('content',''))) for m in history if m.get('role')=='user'): return 'allergy'
    # Preserve a recent hazard when the current request refers back to it.
    if re.search(r'\b(?:it|that|those|this|them|het|dat|dit)\b',q,re.I) and any(hazardous(m.get('content','')) for m in history[-4:] if m.get('role')=='user'): return 'hazard'
    return None

@action(is_system_action=True)
async def chef_input_policy(context=None):
    context=context or {}; q=str(context.get('user_message') or context.get('last_user_message') or '')
    return input_category(q,context.get('chef_history') or []) is not None

@action(is_system_action=True)
async def chef_output_policy(context=None):
    context=context or {}; answer=str(context.get('bot_message') or '')
    if UNSAFE_ASSURANCE.search(answer): return True
    if EGG.search(answer) and UNSAFE_EGG.search(answer): return True
    without_disclaimer=answer.replace('Source cooking steps may contain quantities and timings for the original servings; they have not been scaled.','')
    # Only fixed reviewed templates may supply egg cooking steps; recipe lists
    # and ingredient-only answers remain allowed without this exception.
    if EGG.search(answer) and PREPARATION.search(without_disclaimer) and not approved_egg_answer(answer): return True
    return False
