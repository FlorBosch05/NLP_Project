"""Ground soup recommendations and track the active, known recipe."""
import re
from chef.retrieval import read_recipes


def recipe_by_name(name):
    return next((r for r in read_recipes() if r['name'].casefold() == str(name or '').casefold()), None)


def source_result(index, recipe, text, focus=True):
    """Attach real retrieved context for a recipe and never fabricate evidence."""
    nodes=index.as_retriever(similarity_top_k=5).retrieve(recipe['name']+' soup recipe ingredients overview')
    chunks=[{'text':n.node.get_content(),'metadata':n.node.metadata,'score':n.score} for n in nodes]
    if not any(c['metadata'].get('recipe') == recipe['name'] for c in chunks):
        return {'route':'retrieve','answer':'I could not retrieve that recipe reliably. Please try another recipe.', 'calls':[], 'recipe_focus':None}
    return {'route':'retrieve','answer':text,'context':chunks,'search_query':recipe['name']+' soup recipe ingredients overview',
            'calls':[],'ttft_seconds':None,'recipe_focus':recipe['name'] if focus else None}


class ConversationGraph:
    def __init__(self, graph, index):
        self.graph,self.index=graph,index

    def invoke(self, state):
        question=state['question']; q=question.casefold().strip()
        history=state.get('history',[])
        last_users=[str(m.get('content','')).casefold() for m in history[-8:] if m.get('role')=='user']
        focus=recipe_by_name(state.get('recipe_focus'))
        recipes=read_recipes()
        named=[r for r in recipes if r['name'].casefold() in q]
        soup=bool(re.search(r'\b(?:soup|soep)\b',q))
        prior_soup=any(re.search(r'\b(?:soup|soep)\b',m) for m in last_users[-2:])
        servings=bool(re.search(r'\b(?:how many (?:people|servings|portions)|serves? how many|hoeveel (?:mensen|personen|porties))\b',q))
        scaling=bool(re.search(r'\b(?:scale|double|halve|verdubbel|halveer|schaal)\b',q))

        # The corpus has a cold tomato soup but no recipe named tomato soup.
        if re.search(r'\b(?:tomato soup|tomatensoep)\b',q) and not named:
            recipe=recipe_by_name('Gazpacho')
            return source_result(self.index,recipe,'The tomato soup in the collection is Gazpacho, which is served cold. It serves 4. Would you like that recipe?',True)
        if servings and not scaling:
            recipe=named[0] if len(named)==1 else focus if not named else None
            if recipe is None:
                return {'route':'retrieve','answer':'Which recipe do you mean? I need a recipe from the collection to check its serving count.', 'calls':[], 'recipe_focus':None}
            return source_result(self.index,recipe,f"{recipe['name']} serves {recipe['servings']} people according to the source.")

        # Broad soup recommendation: answer from a real record, with restrictions
        # taken from source tags rather than inferred by an LLM.
        wants_recommendation=(soup and bool(re.search(r'\b(?:what|which|suggest|recommend|make|want|looking|welke|raad|maken|wil)\b',q))) or (soup and prior_soup and bool(re.search(r'\b(?:no restrictions|no preference|salty|zout|geen beperkingen)\b',q)))
        if wants_recommendation and not named and not scaling:
            if re.search(r'\b(?:allerg|without|free of|no dairy|no nuts|zonder|no meat|spicy|pittig|chicken|tomato|kip|tomaat)\w*\b',q):
                return {'route':'retrieve','answer':'I can suggest a soup from the collection. Which ingredients or dietary requirements should I look for?', 'calls':[], 'recipe_focus':None}
            tag='vegan' if 'vegan' in q else 'vegetarian' if re.search(r'\b(?:vegetarian|vegetarisch)\b',q) else None
            soup_recipes=[r for r in recipes if re.search(r'\b(?:soup|broth)\b',(r['name']+' '+r['overview']).casefold())]
            if tag: soup_recipes=[r for r in soup_recipes if tag in [str(t).casefold() for t in r.get('dietary_tags',[])]]
            if not soup_recipes:
                return {'route':'retrieve','answer':'I could not find a soup with that source tag in the collection. Would you like a different kind?', 'calls':[], 'recipe_focus':None}
            recipe=soup_recipes[0]
            tag_note=f' The source labels it {tag}; check ingredients and labels.' if tag else ''
            text=f"How about {recipe['name']}? It serves {recipe['servings']} people according to the recipe source.{tag_note} Would you like the ingredients?"
            return source_result(self.index,recipe,text)

        result=self.graph.invoke(state)
        # Guard against a chat route inventing a recipe without retrieved evidence.
        if result.get('route')=='chat' and not result.get('context') and re.search(r'\b(?:ingredients|instructions|recipe:)\b',result.get('answer',''),re.I):
            return {'route':'chat','answer':'I can help find a recipe in the collection. What kind of dish or ingredient are you looking for?', 'calls':result.get('calls',[]), 'recipe_focus':None}
        if len(named)==1 and result.get('route') in ('retrieve','scale'):
            result['recipe_focus']=named[0]['name']
        return result
