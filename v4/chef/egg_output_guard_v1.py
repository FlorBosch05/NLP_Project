"""Keep unreviewed egg preparation advice out of ordinary model replies."""
import re

EGG=re.compile(r'\b(?:eggs?|egg yolks?|yolks?|eieren?|eigeel|eidooier)\b',re.I)
PROCEDURE=re.compile(r'\b(?:cook|cooked|cooking|fry|frying|fried|heat|bake|baked|stir|mix|whisk|beat|break|crack|raw|runny|loose|soft|set|serve|prepar(?:e|ation)|instructions?|kook|bak|rauw|zacht|gaar)\b',re.I)

class EggOutputGuard:
    def __init__(self,inner): self.inner=inner
    def invoke(self,state):
        result=self.inner.invoke(state)
        answer=result.get('answer','')
        stage=(result.get('safety') or {}).get('stage','')
        # The selection path has reviewed fixed steps for Menemen. The two
        # prior fixed source adaptations contain no egg instructions.
        trusted=stage=='input_checked_structured_selection' or (stage=='reviewed_tortilla_and_output_check')
        if not trusted and EGG.search(answer) and PROCEDURE.search(answer):
            return {'route':'safety_block','answer':'I cannot verify these egg preparation instructions. Please ask for a reviewed egg recipe, such as Menemen.', 'calls':result.get('calls',[]), 'safety':{'stage':'egg_output_review','category':'uncertain'}}
        return result
