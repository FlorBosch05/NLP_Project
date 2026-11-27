"""Safety rail v3: deterministic source-tag and source-time answers."""
import re
from chef.safety_rails_v2 import MESSAGES, check_input, check_output
from chef.retrieval import read_recipes


def source_fact(question):
    """Answer only narrow source-metadata questions from structured V4 data.

    The fixed template does not follow free-form model output. Ambiguous names,
    tags and phrasings fall back to the ordinary guarded graph.
    """
    q = question.strip().casefold()
    recipes = [r for r in read_recipes() if r['name'].casefold() in q]
    if len(recipes) != 1: return None
    recipe = recipes[0]
    recipe_name = re.escape(recipe['name'].casefold())
    time_pattern = rf'what are the source preparation and cooking times for {recipe_name}\??'
    if re.fullmatch(time_pattern, q):
        prep, cook = recipe.get('prep_minutes'), recipe.get('cook_minutes')
        if not isinstance(prep, (int, float)) or not isinstance(cook, (int, float)): return None
        return (f"The source's structured fields list {prep:g} minutes preparation and {cook:g} minutes cooking for {recipe['name']}. "
                'Source descriptions or step timings may differ; these values have not been independently verified.')
    tag_pattern = rf'is {recipe_name} tagged (vegan|vegetarian|gluten-free|pescatarian) in the source\??'
    match = re.fullmatch(tag_pattern, q)
    if match:
        tag = match.group(1)
        tags = {str(t).casefold() for t in recipe.get('dietary_tags', [])}
        verdict = 'is' if tag in tags else 'is not listed as'
        return (f"{recipe['name']} {verdict} {tag} in the source's tags. "
                'Source tags are not independently verified; check ingredients, labels and cross-contact.')
    return None


class GuardedGraph:
    def __init__(self, graph, model):
        self.graph, self.model = graph, model

    def invoke(self, state):
        question = state['question']
        category = check_input(self.model, question, state.get('history', []))
        if category != 'allow':
            return {'route':'safety_block','answer':MESSAGES[category],'calls':[], 'safety':{'stage':'input','category':category}}
        result = self.graph.invoke(state)
        # These narrow templates use validated scalar metadata, not model output.
        # Still perform retrieval so the UI records the source context.
        fact = source_fact(question)
        if fact and result.get('route') == 'retrieve':
            result['answer'] = fact
            # The streamed draft is discarded; it is not the displayed answer.
            result['ttft_seconds'] = None
            result['safety'] = {'stage':'verified_source_template','category':'allow'}
            return result
        category = check_output(self.model, question, result.get('answer', ''))
        if category != 'allow':
            return {'route':'safety_block','answer':MESSAGES[category], 'calls':result.get('calls',[]), 'safety':{'stage':'output','category':category}}
        result['safety'] = {'stage':'passed','category':'allow'}
        return result
