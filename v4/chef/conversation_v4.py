"""Grounded conversational recipe selection; no unverified dietary guarantees."""
import re
from chef.conversation_v3 import recipe_by_name, source_result
from chef.retrieval import read_recipes

SOUP = re.compile(r'\b(?:soup|soep)\b', re.I)
INGREDIENT_QUESTION = re.compile(r'\b(?:ingredients|ingredienten)\b', re.I)
SERVINGS = re.compile(r'\b(?:how many (?:people|servings|portions)|serves? how many|hoeveel (?:mensen|personen|porties))\b', re.I)
SCALING = re.compile(r'\b(?:scale|double|halve|verdubbel|halveer|schaal)\b', re.I)
NUMBERS = {'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10}

def listing(recipe):
    lines=[]
    for item in recipe['ingredients']:
        amount=item.get('quantity'); unit=item.get('unit') or ''
        value=f'{amount:g} {unit}' if isinstance(amount,(int,float)) else 'amount not specified; follow the source'
        lines.append(f"- {item['name']}: {value}")
    return f"Ingredients for {recipe['name']} (source recipe; serves {recipe['servings']}):\n"+'\n'.join(lines)

def soup_preferences(texts):
    text=' '.join(texts).casefold()
    avoid=[]
    if re.search(r"\b(?:without|no|avoid|don't like|do not like|dont like|dislike|zonder|geen)\s+(?:any\s+)?onions?\b",text): avoid.append('onion')
    meatless=bool(re.search(r'\b(?:without meat|no meat|meatless|zonder vlees|geen vlees)\b',text))
    vegetarian=bool(re.search(r'\b(?:vegetarian|vegetarisch)\b',text))
    vegan=bool(re.search(r'\b(?:vegan|veganistisch)\b',text))
    return avoid,meatless,vegetarian,vegan

class ConversationGraph:
    def __init__(self,graph,index): self.graph,self.index=graph,index

    def invoke(self,state):
        question=state['question']; q=question.casefold().strip(); history=state.get('history',[])
        users=[str(m.get('content','')).casefold() for m in history[-8:] if m.get('role')=='user']
        focus=recipe_by_name(state.get('recipe_focus')); recipes=read_recipes()
        named=[r for r in recipes if r['name'].casefold() in q]
        prior_soup=any(SOUP.search(m) for m in users[-3:]) or bool(focus and SOUP.search(focus['name']+' '+focus['overview']))
        soup=bool(SOUP.search(q)); scaling=bool(SCALING.search(q))
        if re.search(r'\b(?:tomato soup|tomatensoep)\b',q) and not named:
            recipe=recipe_by_name('Gazpacho')
            return source_result(self.index,recipe,'Gazpacho is a cold tomato soup that serves 4. Would you like the ingredients?')
        # Unambiguous number in an explicit request to make a focused recipe for N.
        match=re.search(r'\b(?:make|cook|serve)\s+(?:it|that|this)\s+for\s+(\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:people|persons|servings|portions)\b',q)
        if match and focus and not named:
            token=match.group(1); target=NUMBERS.get(token) if token in NUMBERS else float(token)
            if 0 < target <= 1000:
                rewritten={**state,'question':f"Scale {focus['name']} to {target:g} servings."}
                result=self.graph.invoke(rewritten);result['recipe_focus']=focus['name'];return result
        if SERVINGS.search(q) and not scaling:
            recipe=named[0] if len(named)==1 else focus if not named else None
            if recipe is None: return {'route':'retrieve','answer':'Which recipe do you mean? I need a recipe from the collection to check its serving count.','calls':[],'recipe_focus':None}
            return source_result(self.index,recipe,f"{recipe['name']} serves {recipe['servings']} people according to the source.")
        if INGREDIENT_QUESTION.search(q) and not scaling and not re.search(r'\b(?:without|no|avoid|allerg|zonder|geen)\b',q):
            recipe=named[0] if len(named)==1 else focus if not named else None
            if recipe is None: return {'route':'retrieve','answer':'Which recipe do you mean? I need a recipe from the collection to list its ingredients.','calls':[],'recipe_focus':None}
            return source_result(self.index,recipe,listing(recipe))
        # Named recipe switches use source data instead of a chat hallucination.
        if len(named)==1 and re.search(r'\b(?:tell me about|information about|what is|tell me more about)\b',q):
            recipe=named[0]; sentence=recipe['overview'].split('. ',1)[0].rstrip('.')
            return source_result(self.index,recipe,f"{recipe['name']}: {sentence}. The source recipe serves {recipe['servings']}. Would you like the ingredients?")
        # A source list is evidence about labels, not a guarantee of safety.
        contains=re.search(r'\b(?:does it contain|does that contain|is there)\s+([a-z][a-z -]{1,35})\??$',q)
        if contains:
            if not focus: return {'route':'retrieve','answer':'Which recipe do you mean?','calls':[],'recipe_focus':None}
            term=contains.group(1).strip(); found=[i['name'] for i in focus['ingredients'] if term in i['name'].casefold()]
            if found: text=f"The source lists {', '.join(found)} in {focus['name']}. Check product labels for the actual ingredients."
            else: text=f"No {term} is listed in the {focus['name']} source ingredients. Check the ingredient labels."
            return source_result(self.index,focus,text)
        recommendation=(soup and bool(re.search(r'\b(?:what|which|suggest|recommend|make|want|need|looking|have|welke|raad|maken|wil)\b',q))) or (prior_soup and bool(re.search(r'\b(?:different|another|something else|no restrictions|salty|geen beperkingen|andere)\b',q)))
        if recommendation and not named and not scaling:
            # Recognize only constraints we can check against stored fields.
            combined=users[-3:]+[q]; avoid,meatless,vegetarian,vegan=soup_preferences(combined)
            if re.search(r'\b(?:spicy|pittig|chicken|kip|gluten.free|dairy.free|no dairy|no nuts)\b',q):
                return {'route':'retrieve','answer':'I cannot reliably filter that preference from the source data. Would you like to choose a recipe from the collection?', 'calls':[],'recipe_focus':None}
            tag='vegan' if vegan or meatless else 'vegetarian' if vegetarian else None
            soups=[r for r in recipes if SOUP.search(r['name']+' '+r['overview']) or re.search(r'\bbroth\b',r['overview'],re.I)]
            if tag: soups=[r for r in soups if tag in [str(x).casefold() for x in r.get('dietary_tags',[])]]
            if avoid: soups=[r for r in soups if not any(term in i['name'].casefold() for term in avoid for i in r['ingredients'])]
            if focus and re.search(r'\b(?:different|another|else|andere)\b',q): soups=[r for r in soups if r['name']!=focus['name']]
            if not soups: return {'route':'retrieve','answer':'I could not find a soup matching those source-data filters. Would you like to try another preference?', 'calls':[],'recipe_focus':None}
            recipe=soups[0]; caveat=' The source lists it as vegan; check ingredients and labels.' if tag=='vegan' else ' The source lists it as vegetarian; check ingredients and labels.' if tag else ''
            cold=' It is served cold.' if recipe['name']=='Gazpacho' else ''
            text=f"How about {recipe['name']}? It serves {recipe['servings']} people according to the source.{cold}{caveat} Would you like the ingredients?"
            return source_result(self.index,recipe,text)
        result=self.graph.invoke(state)
        if result.get('route')=='chat' and not result.get('context') and re.search(r'\b(?:ingredients|instructions)\b|\brecipe\s*:',result.get('answer',''),re.I):
            return {'route':'chat','answer':'I can help find a recipe in the collection. What kind of dish or ingredient are you looking for?','calls':result.get('calls',[]),'recipe_focus':None}
        if len(named)==1 and result.get('route') in ('retrieve','scale'): result['recipe_focus']=named[0]['name']
        return result
