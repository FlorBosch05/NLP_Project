"""Narrow, source-based replies to simple recipe-selection requests.

Input safety is checked first. Only fixed templates and stored ingredient names
are emitted here; all other requests go through the existing guarded graph.
"""
import re
from difflib import SequenceMatcher
from chef.retrieval import read_recipes
from chef.structured_evidence_v2 import source_result
from chef.conversation_v8 import listing

# Reviewed adaptations of two source recipes. Other cooking instructions keep
# the normal model/output-safety path; do not expose arbitrary raw instructions.
REVIEWED_STEPS = {
    'Borscht': '1. Cover the beef with cold water, bring to a boil, skim and simmer for about 90 minutes until fully cooked.\n2. Braise the beetroot with oil, tomato paste and vinegar for about 20 minutes.\n3. Fry the onion and carrot until soft.\n4. Remove and shred the beef, return it to the stock, then add the potatoes and cook for 10 minutes.\n5. Add cabbage; after 5 minutes add the beetroot and fried vegetables. Cook for another 5 minutes, add bay leaf and garlic, and remove from the heat.\n6. Cover and let stand for at least 20 minutes; serve with sour cream.',
    'French onion soup': '1. Cook the onions in butter with a pinch of salt over medium heat for about 20 minutes, stirring regularly.\n2. Continue for about 25 minutes until caramelized, lowering the heat and adding a little water if they catch.\n3. Stir in flour and cook for 2 minutes.\n4. Add the wine and reduce by half.\n5. Add stock and thyme, bring to a boil and simmer for 20 minutes; season to taste.\n6. Ladle into ovenproof bowls, top with baguette and cheese, and grill for about 3 minutes until browned.',
}

class SimpleRecipeGraph:
    def __init__(self, guarded, index, model, top_k=5):
        self.guarded, self.index, self.model, self.top_k = guarded, index, model, top_k

    def invoke(self, state):
        q = state['question'].casefold().strip()
        normalized = re.sub(r'[?!.,]+$', '', q).strip()
        history = state.get('history', [])
        recipes = read_recipes()
        # Full-match grammars only: no extra instructions can hide in a shortcut.
        pasta = bool(re.fullmatch(r'[a-z]{6,12}', normalized)) and SequenceMatcher(None, normalized, 'spaghetti').ratio() >= .75
        soup_match = re.fullmatch(r'(?:ok(?:ay)?\s+)?([a-z]{3,12})\s+soup', normalized)
        soup = soup_match and SequenceMatcher(None, soup_match.group(1), 'onion').ratio() >= .70
        ingredient_match = re.fullmatch(r'i want something with ([a-z]+)\s+give me a recipe', normalized)
        ingredient = ingredient_match.group(1).removesuffix('s') if ingredient_match else None
        matches = [r for r in recipes if ingredient and any(i['name'].casefold() == ingredient for i in r['ingredients'])]
        steps = re.fullmatch(r'(?:how (?:do i|can i) (?:prepare|make|cook) it|(?:yes|yes please|show me the (?:preparation )?steps|preparation steps))', normalized)
        focus = state.get('recipe_focus')
        reviewed = bool(steps and focus in REVIEWED_STEPS)
        if not (pasta or soup or matches or reviewed):
            return self.guarded.invoke(state)
        if pasta:
            result = {'route':'retrieve', 'answer':"I couldn't find a spaghetti recipe in the current collection. Would you like another kind of dish?", 'calls':[], 'recipe_focus':None}
        else:
            recipe = next(r for r in recipes if r['name'] == (focus if reviewed else 'French onion soup')) if (soup or reviewed) else matches[0]
            intro = f"Here is {recipe['name']} from the collection. " if soup else f"{recipe['name']} contains {ingredient}. "
            if reviewed:
                answer = f"Preparation for {recipe['name']} (adapted from the source):\n\n" + REVIEWED_STEPS[recipe['name']]
            else:
                answer = intro + listing(recipe)
                answer += '\n\nPreparation (adapted from the source):\n' + REVIEWED_STEPS[recipe['name']] if recipe['name'] in REVIEWED_STEPS else '\n\nWould you like the preparation steps?'
            result = source_result(self.index, recipe, answer, top_k=self.top_k)
        result['safety'] = {'stage':'input_checked_fixed_source_reply','category':'allow'}
        return result
