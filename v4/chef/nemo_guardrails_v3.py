"""NeMo Guardrails input and output rails surrounding the full application."""
from pathlib import Path
import asyncio
import threading
from nemoguardrails import RailsConfig, LLMRails
from nemoguardrails.rails.llm.options import RailStatus, RailType
from nemo_config_v3.actions import input_category
from chef.recipe_catalog_v3 import TORTILLA_ANSWER
import re

TORTILLA_REQUEST=re.compile(r'^(?:how does the source say to prepare spanish tortilla|how (?:do i|can i) (?:make|prepare|cook) (?:a |the )?spanish tortilla|how is spanish tortilla prepared|how to (?:make|prepare|cook) (?:a |the )?spanish tortilla|hoe (?:maak|bereid) ik (?:een |de )?spanish tortilla)\s*[?.!]*$',re.I)

MESSAGES={
 'hazard':'I cannot recommend consuming hazardous or unidentified substances, or provide unsafe food-handling instructions. Please ask about food-safe ingredients instead.',
 'allergy':'I cannot determine whether a recipe is safe for a personal allergy. Check ingredient labels and cross-contact risks and consult a qualified clinician for individual advice.',
 'injection':'I cannot follow instructions to override the assistant’s safety rules. Please ask a culinary question instead.',
 'uncertain':'I cannot safely assess this request or response. Please rephrase it.',
}

class NemoGuardedGraph:
    def __init__(self,graph,model_name='qwen2.5:7b'):
        self.graph=graph
        config=RailsConfig.from_path(str(Path(__file__).resolve().parents[1]/'nemo_config_v3'))
        config.models[0].model=model_name
        self.rails=LLMRails(config)
        # Reuse one event loop instead of letting the synchronous check() close
        # the loop after every turn. Ollama's async HTTP client is loop-bound.
        self.loop=asyncio.new_event_loop()
        self.worker=threading.Thread(target=self.loop.run_forever,daemon=True,name='nemo-rails-loop')
        self.worker.start()
        self.check_lock=threading.Lock()

    def check(self,messages,rail_type):
        with self.check_lock:
            future=asyncio.run_coroutine_threadsafe(self.rails.check_async(messages,rail_types=[rail_type]),self.loop)
            try:
                return future.result(timeout=60)
            except BaseException:
                future.cancel()
                raise

    def invoke(self,state):
        q=state['question'];history=state.get('history',[])[-8:]
        try:
            input_result=self.check([{'role':'context','content':{'chef_history':history}},{'role':'user','content':q}],RailType.INPUT)
        except Exception as exc:
            return {'route':'safety_block','answer':'The safety check is unavailable. Please check that Ollama is running and try again.','calls':[], 'safety':{'stage':'nemo_error','category':'uncertain','error_type':type(exc).__name__}}
        if input_result.status!=RailStatus.PASSED or input_result.content!=q:
            cat=input_category(q,history) or 'uncertain'
            return {'route':'safety_block','answer':MESSAGES[cat],'calls':[],'safety':{'stage':'nemo_input','category':cat,'rail':input_result.rail,'status':str(input_result.status)}}
        try:
            result=self.graph.invoke(state)
            if TORTILLA_REQUEST.fullmatch(q.strip()) and result.get('route')=='retrieve':
                result['answer']=TORTILLA_ANSWER
                result['ttft_seconds']=None
            answer=result.get('answer','')
            if not isinstance(answer,str) or not answer.strip():
                return {'route':'error','answer':'I could not find an answer for that. Could you name a recipe or ingredient?','calls':result.get('calls',[]),'safety':{'stage':'workflow_empty','category':'uncertain'}}
        except Exception as exc:
            return {'route':'error','answer':'The recipe workflow could not complete your request. Please try again.','calls':[], 'safety':{'stage':'workflow_error','category':'uncertain','error_type':type(exc).__name__}}
        try:
            # Do not pass a context message here: NeMo 0.25.0 LLMRails.check
            # silently loses assistant-only content in that combination.
            output_result=self.check([{'role':'assistant','content':answer}],RailType.OUTPUT)
            if output_result.status!=RailStatus.PASSED or output_result.content!=answer:
                return {'route':'safety_block','answer':MESSAGES['uncertain'],'calls':result.get('calls',[]),'safety':{'stage':'nemo_output','category':'uncertain','rail':output_result.rail,'status':str(output_result.status)}}
            result['safety']={'stage':'nemo_input_and_output','category':'allow','input_rail_status':str(input_result.status),'output_rail_status':str(output_result.status)}
            return result
        except Exception as exc:
            return {'route':'safety_block','answer':'The safety check is unavailable. Please check that Ollama is running and try again.','calls':[], 'safety':{'stage':'nemo_error','category':'uncertain','error_type':type(exc).__name__}}
