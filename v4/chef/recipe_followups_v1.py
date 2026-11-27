"""Resolve short acknowledgements against an explicit previous offer and focus.

The outer NeMo rails still check the original user message and final answer.
This wrapper never treats an affirmative as approval of a safety exception.
"""
import re
from chef.retrieval import read_recipes
from chef.conversation_v8 import listing
from chef.structured_evidence_v2 import source_result

YES = re.compile(r"^(?:yes|yeah|yep|yup|sure|ok(?:ay)?|ja|jazeker|graag|doe maar|yes please|ja graag)\b(?:[\s,]+(?:please|sure|thanks|thank you|do|mar|maar|graag|yes|ja))*[.!?]*$", re.I)
DETAILS = re.compile(r"\b(?:what(?:'s| is) the recipe|give me the recipe|show me the recipe|how (?:do i|can i) (?:make|cook) it|wat is het recept|geef me het recept|hoe maak ik het)\b",re.I)
OFFER = re.compile(r"(?:would you like|do you want|shall i (?:show|give)|wil je|wilt u).{0,45}\b(?:ingredients|ingredienten|ingrediënten)\b",re.I)

class RecipeFollowupsGraph:
    def __init__(self,inner,index,top_k=5): self.inner,self.index,self.top_k=inner,index,top_k
    def invoke(self,state):
        q=state['question']; history=state.get('history',[])
        last=next((str(m.get('content','')) for m in reversed(history) if m.get('role')=='assistant'),'')
        recipes=read_recipes()
        recipe=next((r for r in recipes if r['name']==state.get('recipe_focus')),None)
        named_elsewhere=any(r['name']!=state.get('recipe_focus') and r['name'].casefold() in q.casefold() for r in recipes)
        if recipe and not named_elsewhere and DETAILS.search(q) and not re.search(r'\b(?:another|other|different|ander|andere)\b',q,re.I):
            # Reuse the named catalogue path: it has reviewed steps where
            # available and clearly states when they are not yet reviewed.
            rewritten={**state,'question':'give me the recipe for '+recipe['name']}
            return self.inner.invoke(rewritten)
        if recipe and YES.fullmatch(q.strip()) and OFFER.search(last):
            return source_result(self.index,recipe,listing(recipe),top_k=self.top_k)
        return self.inner.invoke(state)
