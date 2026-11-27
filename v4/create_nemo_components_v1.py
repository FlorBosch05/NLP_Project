"""Create separate business-logic copies without the previous safety wrappers."""
from pathlib import Path
root=Path(__file__).resolve().parent/'chef'
def write(source,dest,replacements):
 text=(root/source).read_text(encoding='utf-8')
 for old,new in replacements:
  if old not in text: raise RuntimeError(f'Expected text missing in {source}: {old[:70]!r}')
  text=text.replace(old,new)
 (root/dest).write_text(text,encoding='utf-8')

write('conversation_shortcuts_v1.py','conversation_shortcuts_v2.py',[
 ("from chef.safety_checks_v5 import MESSAGES, check_input\n",''),
 ("        category = check_input(self.model, state['question'], history)\n        if category != 'allow':\n            return {'route':'safety_block','answer':MESSAGES[category],'calls':[], 'safety':{'stage':'input','category':category}}\n",''),
])
write('ingredient_selection_v1.py','ingredient_selection_v2.py',[
 ("from chef.safety_checks_v5 import ALLERGY, HAZARD, MESSAGES, check_input\n",''),
 ((root/'ingredient_selection_v1.py').read_text(encoding='utf-8').split('def fresh_topic_history(history):',1)[1].split('class IngredientSelectionGraph:',1)[0].join(['def fresh_topic_history(history):','class IngredientSelectionGraph:']), 'class IngredientSelectionGraph:'),
 ("            category=check_input(self.model,question,fresh_topic_history(history))\n            if category!='allow': return {'route':'safety_block','answer':MESSAGES[category],'calls':[], 'safety':{'stage':'input','category':category}}\n",''),
 ("        safety_history=history if other else fresh_topic_history(history)\n        category=check_input(self.model,question,safety_history)\n        if category!='allow': return {'route':'safety_block','answer':MESSAGES[category],'calls':[], 'safety':{'stage':'input','category':category}}\n",''),
 ("The temperature step is a food-safety adaptation; the source calls for a loose yolk.","The temperature step is a food-safety adaptation."),
])
write('recipe_catalog_v1.py','recipe_catalog_v2.py',[
 ("from chef.safety_checks_v5 import ALLERGY, HAZARD, INJECTION, MESSAGES\n",''),
 ("from chef.ingredient_selection_v1 import canonical, STEPS", "from chef.ingredient_selection_v2 import canonical, STEPS"),
 ("from chef.conversation_shortcuts_v1 import REVIEWED_STEPS", "from chef.conversation_shortcuts_v2 import REVIEWED_STEPS"),
 ("from chef.safety_rails_v9 import TORTILLA_ANSWER", "TORTILLA_ANSWER = 'Gently cook potatoes and onions in olive oil, drain, then combine with beaten eggs. Cook in a pan, flip and cook until the centre reaches 71°C (160°F), measured with a food thermometer. Recipe adapted from UniTools, CC BY-SA 4.0. The temperature check is a food-safety adaptation based on FoodSafety.gov.'"),
 ("        if INJECTION.search(question): return {'route':'safety_block','answer':MESSAGES['injection'],'calls':[], 'safety':{'stage':'input','category':'injection'}}\n        if HAZARD.search(question): return {'route':'safety_block','answer':MESSAGES['hazard'],'calls':[], 'safety':{'stage':'input','category':'hazard'}}\n        if ALLERGY.search(question) or any(ALLERGY.search(str(m.get('content',''))) for m in history[-8:] if m.get('role')=='user'):\n            return {'route':'safety_block','answer':MESSAGES['allergy'],'calls':[], 'safety':{'stage':'input','category':'allergy'}}\n",''),
])
