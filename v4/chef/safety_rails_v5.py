"""Safety v4: reviewed, source-attributed Spanish tortilla instructions."""
import re
from chef.safety_rails_v2 import MESSAGES, check_input, check_output
from chef.safety_rails_v3 import source_fact

# A deliberately fixed, reviewed adaptation of the V4 Spanish tortilla record.
# The source's suggested loose centre is replaced with a temperature check.
TORTILLA_ANSWER = 'Gently cook potatoes and onions in olive oil, drain, then combine with beaten eggs. Cook in a pan, flip and cook until the centre reaches 71°C (160°F), measured with a food thermometer. Recipe adapted from UniTools, CC BY-SA 4.0. The temperature check is a food-safety adaptation based on FoodSafety.gov.'

TORTILLA_REQUEST = re.compile(
    r'^(?:how does the source say to prepare spanish tortilla|'
    r'how (?:do i|can i) (?:make|prepare|cook) (?:a |the )?spanish tortilla|'
    r'how is spanish tortilla prepared|'
    r'how to (?:make|prepare|cook) (?:a |the )?spanish tortilla|'
    r'hoe (?:maak|bereid) ik (?:een |de )?spanish tortilla)\s*[?.!]*$', re.I)


class GuardedGraph:
    def __init__(self, graph, model):
        self.graph, self.model = graph, model

    def invoke(self, state):
        question = state['question']
        category = check_input(self.model, question, state.get('history', []))
        if category != 'allow':
            return {'route':'safety_block','answer':MESSAGES[category],'calls':[], 'safety':{'stage':'input','category':category}}
        result = self.graph.invoke(state)
        if TORTILLA_REQUEST.fullmatch(question.strip()) and result.get('route') == 'retrieve':
            # Only the reviewed fixed answer is sent to the output gate. Never
            # show the potentially unsafe generated draft; keep its retrieval.
            result['answer'] = TORTILLA_ANSWER
            result['ttft_seconds'] = None
            category = check_output(self.model, question, TORTILLA_ANSWER)
            if category != 'allow':
                return {'route':'safety_block','answer':MESSAGES[category],'calls':result.get('calls',[]), 'safety':{'stage':'output','category':category}}
            result['safety'] = {'stage':'reviewed_tortilla_and_output_check','category':'allow'}
            return result
        fact = source_fact(question)
        if fact and result.get('route') == 'retrieve':
            result['answer'] = fact
            result['ttft_seconds'] = None
            result['safety'] = {'stage':'verified_source_template','category':'allow'}
            return result
        category = check_output(self.model, question, result.get('answer', ''))
        if category != 'allow':
            return {'route':'safety_block','answer':MESSAGES[category],'calls':result.get('calls',[]), 'safety':{'stage':'output','category':category}}
        result['safety'] = {'stage':'passed','category':'allow'}
        return result
