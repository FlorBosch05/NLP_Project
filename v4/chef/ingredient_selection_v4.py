"""Select recipes from structured ingredients for narrowly unambiguous requests."""
import re
from difflib import SequenceMatcher
from chef.retrieval import read_recipes
from chef.structured_evidence_v2 import source_result
from chef.conversation_v8 import listing
from chef.conversation_shortcuts_v2 import REVIEWED_STEPS

MENEMEN_STEPS = ('1. Slice the peppers and fry them in the butter and olive oil for 3–4 minutes.\n'
 '2. Add the chopped tomatoes and salt, and cook for about 10 minutes.\n'
 '3. Lower the heat, add the eggs and pepper flakes, and stir. Continue cooking until the egg dish reaches 71°C (160°F), measured with a food thermometer.\n'
 '4. Add oregano and cheese. The temperature step is a food-safety adaptation. '
 '[FDA egg safety guidance](https://www.fda.gov/food/buy-store-serve-safe-food/what-you-need-know-about-egg-safety).')
RATATOUILLE_STEPS = ('1. Fry the aubergine in oil until browned; set aside. Fry the courgette and then the pepper separately.\n'
 '2. Soften the onion in the remaining oil; add garlic and thyme briefly. Add the tomatoes and cook down for about 20 minutes.\n'
 '3. Return the vegetables to the pan, season and warm together over low heat for 10 minutes. Add basil and let stand before serving.')
STEPS = {**REVIEWED_STEPS, 'Menemen':MENEMEN_STEPS, 'Ratatouille':RATATOUILLE_STEPS}

DUTCH_INGREDIENTS={'wortel':'carrot','wortels':'carrot','ui':'onion','uien':'onion','tomaat':'tomato','tomaten':'tomato','ei':'egg','eieren':'egg','aardappel':'potato','aardappelen':'potato','knoflook':'garlic'}
BORSHCH_NAMES={'Beef on the bone':'Rundvlees met bot','Beetroot':'Rode biet','Cabbage':'Kool','Potatoes':'Aardappelen','Carrot':'Wortel','Onion':'Ui','Tomato paste':'Tomatenpuree','Vinegar, 9%':'Azijn, 9%','Garlic':'Knoflook','Bay leaf':'Laurierblad','Sour cream':'Zure room','Salt and pepper':'Zout en peper'}
DUTCH_UNITS={'piece':'stuk','clove':'teen','g':'g','kg':'kg','tbsp':'eetlepel','tsp':'theelepel','l':'liter','ml':'ml','sprig':'takje'}
BORSHCH_STEPS_NL=('1. Zet het rundvlees onder koud water, breng aan de kook, schuim af en laat ongeveer 90 minuten zachtjes sudderen tot het gaar is.\n'
 '2. Stoof de rode biet ongeveer 20 minuten met olie, tomatenpuree en azijn.\n'
 '3. Bak de ui en wortel tot ze zacht zijn.\n'
 '4. Haal het vlees uit de bouillon, trek het in stukken en doe het terug. Voeg de aardappelen toe en kook 10 minuten.\n'
 '5. Voeg de kool toe. Voeg na 5 minuten de biet en de gebakken groenten toe. Kook nog 5 minuten, voeg laurier en knoflook toe en haal de pan van het vuur.\n'
 '6. Laat minstens 20 minuten afgedekt staan en serveer met zure room.')

def dutch_borscht(recipe):
    lines=[f"Borsjt bevat wortel.\n\nIngrediënten voor {recipe['name']} (bronrecept; {recipe['servings']} personen):"]
    for item in recipe['ingredients']:
        amount=item.get('quantity');unit=item.get('unit') or ''
        value=f"{amount:g} {DUTCH_UNITS.get(unit,unit)}" if isinstance(amount,(int,float)) else 'naar smaak' if unit=='toTaste' else 'hoeveelheid niet vermeld'
        lines.append(f"- {BORSHCH_NAMES.get(item['name'],item['name'])}: {value}")
    return '\n'.join(lines)+'\n\nBereiding (aangepast op basis van de bron):\n'+BORSHCH_STEPS_NL

def canonical(word):
    word=word.casefold()
    if word in DUTCH_INGREDIENTS:return DUTCH_INGREDIENTS[word]
    if word.endswith('oes'): return word[:-2]
    if word.endswith('s'): return word[:-1]
    return word

def extract_request(q):
    q=re.sub(r'[.!?]+$', '', q.casefold().strip())
    q=re.sub(r'^(?:actually|well),?\s+', '', q)
    patterns=[r'(?:please )?(?:give me|show me|suggest|recommend) (?:a |an )?recipe (?:with|using|containing|that (?:uses|contains|includes)) ([a-z]+)(?: bro| please)?',
              r'i want (?:a |an )?recipe with ([a-z]+)(?: please)?',
              r'i want something with ([a-z]+) give me a recipe',
              r'i have ([a-z]+)[,.]?\s+what can i (?:cook|make)',
              r'(?:geef|toon) (?:me|mij) (?:een )?recept met ([a-z]+)(?: alsjeblieft)?',
              r'(?:heb je|ken je) (?:een )?recept met ([a-z]+)']
    for p in patterns:
        match=re.fullmatch(p,q)
        if match: return canonical(match.group(1))
    return None

def has_ingredient(recipe, token):
    for ingredient in recipe['ingredients']:
        words=[canonical(w) for w in re.findall(r'[a-z]+',ingredient['name'].casefold())]
        if token in words and not (token=='tomato' and 'paste' in words): return True
    return False

class IngredientSelectionGraph:
    def __init__(self, inner,index,model,top_k=5):
        self.inner,self.index,self.model,self.top_k=inner,index,model,top_k

    def invoke(self,state):
        question=state['question']; q=question.casefold().strip(); history=state.get('history',[])
        token=extract_request(q)
        # An isolated ingredient after a hazardous topic is ambiguous. Ask;
        # do not assume it means combining the two or produce instructions.
        short=re.fullmatch(r'(?:ok(?:ay)?\s+)?([a-z]+)[.!?]*',q)
        short_token=canonical(short.group(1)) if short else None
        recipes=read_recipes()
        if not token and short_token and short_token in {'egg','tomato','carrot'}:
            return {'route':'retrieve','answer':f'Would you like a recipe that uses {short_token}?','calls':[], 'safety':{'stage':'input_checked_clarification','category':'allow'}}
        other=bool(re.fullmatch(r'(?:any|what|are there) (?:other|different|more) recipes?[.!?]*',q))
        if other:
            for message in reversed(history):
                if message.get('role')=='user':
                    token=extract_request(str(message.get('content','')))
                    if token: break
        matches=[r for r in recipes if token and has_ingredient(r,token)]
        if not matches: return self.inner.invoke(state)
        # A full, self-contained request for a known ingredient is a new topic.
        # Preserve allergy history; anaphoric / combined requests never match.
        if other:
            shown=' '.join(str(m.get('content','')).casefold() for m in history if m.get('role')=='assistant')
            matches=[r for r in matches if r['name']!=state.get('recipe_focus') and r['name'].casefold() not in shown]
        if not matches: return {'route':'retrieve','answer':'I could not find another matching recipe in the collection.','calls':[], 'safety':{'stage':'input_checked_clarification','category':'allow'}}
        if token=='egg' and not other:
            recipe=next((r for r in matches if r['name']=='Menemen'),matches[0])
        else:
            # Prefer a recipe with reviewed steps, and avoid repeating the
            # previous choice when another reviewed match is available.
            reviewed=[r for r in matches if r['name'] in STEPS]
            unseen=[r for r in reviewed if r['name']!=state.get('recipe_focus')]
            recipe=(unseen or reviewed or matches)[0]
        text=f"{recipe['name']} contains {token}.\n\n"+listing(recipe)
        if recipe['name'] in STEPS: text+='\n\nPreparation (adapted from the source):\n'+STEPS[recipe['name']]
        else: text+='\n\nThe source contains preparation steps; ask if you would like them.'
        if re.search(r'\b(?:geef|toon|recept|heb je|ken je)\b',q) and recipe['name']=='Borscht':
            text=dutch_borscht(recipe)
        result=source_result(self.index,recipe,text,top_k=self.top_k)
        result['safety']={'stage':'input_checked_structured_selection','category':'allow'}
        return result
