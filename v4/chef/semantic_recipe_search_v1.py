"""Interpret varied ingredient requests with local Qwen and validate the result.

This runs inside NeMo's input/output checks. Qwen proposes intent and constraints;
only ingredients explicitly present in the user messages and in the catalogue
may be used. Actual matching and evidence come from the structured recipe data.
"""
import json,re
from typing import Literal
from pydantic import BaseModel,Field
from langchain_core.messages import HumanMessage,SystemMessage
from chef.retrieval import read_recipes
from chef.conversation_v8 import listing
from chef.ingredient_selection_v4 import canonical,extract_request,STEPS,dutch_borscht
from chef.recipe_catalog_v4 import list_request,named_request,record,ingredient_in_record

ALIASES={'worteltjes':'carrot','wortelen':'carrot','aardappels':'potato','aardappelen':'potato','aardappel':'potato','tomaat':'tomato','tomaten':'tomato','ui':'onion','uien':'onion','eitjes':'egg','eieren':'egg','ei':'egg','knoflook':'garlic','kip':'chicken'}
STOP={'and','or','for','of','with','the','on','in','to','a','an','andere','een','of','stuk','per','small','fresh','dried','thin','dry','sliced','plain','neutral','ground','whole','large','red','green','white','black','extra','virgin','all','bone','piece','pieces','stock','water'}
class SearchIntent(BaseModel):
    intent: Literal['recommend','list','alternative','none'] = Field(description='Whether the user asks for recipe recommendations or a list, asks for an alternative, or something else')
    include: list[str] = Field(default_factory=list,description='Explicit requested ingredients using the supplied canonical candidate names')
    exclude: list[str] = Field(default_factory=list,description='Explicitly rejected ingredients using supplied canonical candidate names')
    diet: Literal['none','vegetarian','vegan'] = Field(default='none',description='Only when the user explicitly requests a vegetarian or vegan dish')

def normal(word):
    return ALIASES.get(word.casefold(),canonical(word.casefold()))

def candidate_tokens(recipes,text):
    inventory={normal(w) for r in recipes for item in r['ingredients'] for w in re.findall(r'[a-z]+',item['name'].casefold()) if w not in STOP and len(w)>2}
    return {normal(w) for w in re.findall(r'[a-z]+',text.casefold()) if normal(w) in inventory}

def explicit_exclusions(text,candidates):
    found=set();unsupported=set()
    text=re.sub(r"\b(?:no restrictions|no preferences|no idea|not sure|don't know|do not know|geen beperkingen|geen idee)\b",'',text.casefold())
    for m in re.finditer(r"\b(?:without|no|not|except|excluding|exclude|avoid|avoiding|skip|leave out|dislike|hate|can't stand|don't like|do not like|don't want|do not want|don't use|do not use|zonder|geen)\s+(?:any\s+)?([a-z]+)",text):
        value=normal(m.group(1))
        if value in candidates:found.add(value)
        else:unsupported.add(value)
    for m in re.finditer(r'\b([a-z]+)[- ]free\b',text):
        value=normal(m.group(1))
        if value in candidates:found.add(value)
        else:unsupported.add(value)
    return found,unsupported

class SemanticRecipeGraph:
    def __init__(self,inner,model):self.inner,self.model=inner,model
    def invoke(self,state):
        q=state['question'];history=state.get('history',[]);recipes=read_recipes()
        previous=[str(m.get('content','')) for m in history[-8:] if m.get('role')=='user']
        prior_text=' '.join(previous[-3:])
        prior_candidates=candidate_tokens(recipes,prior_text)
        prior_exclusions,prior_unsupported=explicit_exclusions(prior_text,prior_candidates)
        if re.search(r'\b(?:no restrictions|no preferences|anything is fine|geen beperkingen)\b',q,re.I):
            prior_exclusions=set();prior_unsupported=set()
        current_candidates=candidate_tokens(recipes,q)
        direct_exclusions,direct_unsupported=explicit_exclusions(q,current_candidates|prior_exclusions)
        # Keep explicit known actions, source facts, serving/scaling, soup
        # conversation handling and direct catalogue lookups on their existing
        # path only when they do not conflict with retained user preferences.
        named=[r for r in recipes if r['name'].casefold() in q.casefold()]
        if named:
            if prior_unsupported or direct_unsupported:
                return {'route':'retrieve','answer':'I can check specific ingredients in the recipe collection. Which ingredient would you like me to leave out?', 'calls':[],'recipe_focus':None}
            excluded=prior_exclusions|direct_exclusions
            conflicts=[t for t in sorted(excluded) if len(named)==1 and ingredient_in_record(named[0],t)]
            if conflicts:
                answer=f"The source ingredients for {named[0]['name']} include {', '.join(conflicts)}. Would you like a different recipe?"
                return {'route':'retrieve','answer':answer,'context':[record(named[0])],'recipe_focus':None,'calls':[]}
            return self.inner.invoke(state)
        if (extract_request(q) or list_request(q) or named_request(q,recipes)) and not (prior_exclusions or prior_unsupported or direct_exclusions or direct_unsupported):return self.inner.invoke(state)
        if re.search(r'\b(?:double|halve|scale|verdubbel|halveer|schaal|servings|portions|personen|porties|allerg|soep|soup)\b',q,re.I):return self.inner.invoke(state)
        if any(re.search(r'\b(?:soup|soep)\b',m,re.I) for m in previous[-3:]) and re.fullmatch(r'(?:something|anything|iets)\s+(?:without|zonder|geen)\s+[a-z]+(?:\s+please)?[.!?]*',q.strip(),re.I):return self.inner.invoke(state)
        request_signal=re.search(r'\b(?:recipe|recipes|dish|dishes|dinner|meal|cook|make|suggest|recommend|ideas|something|anything|recept|recepten|gerecht|gerechten|koken|maken|klaarmaken|idee|ideeën|iets|anders|other|another|else|different)\b',q,re.I)
        preference_followup=bool(previous and re.search(r"\b(?:without|no|not|except|exclude|avoid|avoiding|skip|leave out|dislike|hate|don't like|don't want|don't use|zonder|geen)\b",q,re.I))
        if not request_signal and not preference_followup:return self.inner.invoke(state)
        is_alternative=bool(re.search(r'\b(?:other|another|else|different|anders|andere)\b',q,re.I))
        earlier=' '.join(previous[-3:]) if is_alternative else ''
        candidates=current_candidates|candidate_tokens(recipes,earlier)|prior_exclusions
        if not candidates:return self.inner.invoke(state)
        direct_exclusions,direct_unsupported=explicit_exclusions(q,candidates)
        if direct_unsupported or prior_unsupported:
            return {'route':'retrieve','answer':'I can check specific ingredients in the recipe collection. Which ingredient would you like me to leave out?', 'calls':[],'recipe_focus':None,'safety':{'stage':'semantic_clarification','category':'allow'}}
        if current_candidates & prior_exclusions and not direct_exclusions:
            return {'route':'retrieve','answer':'You previously asked to avoid that ingredient. Would you like to include it now?', 'calls':[],'recipe_focus':None,'safety':{'stage':'semantic_clarification','category':'allow'}}
        if direct_exclusions and not (current_candidates-direct_exclusions) and not is_alternative:
            excluded=direct_exclusions|prior_exclusions
            prior_positive=prior_candidates-prior_exclusions
            requested=prior_positive if len(prior_positive)==1 else set()
            matches=[r for r in recipes if all(ingredient_in_record(r,t) for t in requested) and not any(ingredient_in_record(r,t) for t in excluded)]
            if not matches:return {'route':'retrieve','answer':'I could not find a recipe with those preferences. What would you like to change?','calls':[],'recipe_focus':None,'safety':{'stage':'semantic_clarification','category':'allow'}}
            reviewed=[r for r in matches if r['name'] in STEPS];recipe=(reviewed or matches)[0]
            answer=f"How about {recipe['name']}? Its recorded ingredients do not list {', '.join(sorted(excluded))}. The source recipe serves {recipe['servings']}. Would you like the ingredients?"
            query=f"structured lookup: include={','.join(sorted(requested)) or '(any)'}; exclude={','.join(sorted(excluded))}"
            return {'route':'retrieve','answer':answer,'context':[record(recipe)],'search_query':query,'recipe_focus':recipe['name'],'calls':[],'safety':{'stage':'semantic_catalogue','category':'allow'}}
        instruction=('Extract recipe search intent. Use ONLY candidate names, and only ingredients explicitly requested by the user. '
         'Keep exclusions separate from desired ingredients. Use prior user messages only to resolve an alternative or a continuing preference. '
         'If the user is asking about a safety risk, a calculation, or something other than finding a dish, choose none. '
         'Return list for a request for multiple options, alternative for another dish, recommend for one suggestion. '
         'A diet must be explicitly requested; never infer vegan or vegetarian merely from vegetables.')
        payload={'current_question':q,'recent_user_messages':previous[-3:],'candidate_ingredients':sorted(candidates)}
        try:
            decision=self.model.with_structured_output(SearchIntent,method='json_schema').invoke([SystemMessage(content=instruction),HumanMessage(content=json.dumps(payload,ensure_ascii=False))])
        except Exception:return self.inner.invoke(state)
        if not isinstance(decision,SearchIntent) or decision.intent=='none':return self.inner.invoke(state)
        include={normal(x.strip()) for x in decision.include};exclude={normal(x.strip()) for x in decision.exclude}
        if not include.issubset(candidates) or not exclude.issubset(candidates):return self.inner.invoke(state)
        # A clear request for another option can inherit one unambiguous
        # ingredient from the recent user request, even if Qwen omitted it.
        if is_alternative and not include and not current_candidates:
            previous_candidates=candidate_tokens(recipes,earlier)
            if len(previous_candidates)==1:include=previous_candidates
        if not include and len(current_candidates)==1 and not direct_exclusions and re.search(r'\b(?:using|use|with|featuring|contains|containing|include|including|met)\b',q,re.I):
            include=set(current_candidates)
        # Explicit negations override the model to avoid suggesting a rejected
        # ingredient even if the model puts it in the inclusion list.
        explicit,unsupported=explicit_exclusions(q+' '+earlier,candidates)
        if unsupported:
            return {'route':'retrieve','answer':'I can check specific ingredients in the recipe collection. Which ingredient would you like me to leave out?', 'calls':[],'recipe_focus':None,'safety':{'stage':'semantic_clarification','category':'allow'}}
        exclude |= explicit|prior_exclusions;include-=exclude
        if not include:
            return {'route':'retrieve','answer':'What ingredient would you like the recipe to use?','calls':[],'recipe_focus':None,'safety':{'stage':'semantic_clarification','category':'allow'}}
        diet=decision.diet
        if diet!='none' and not re.search(r'\b(?:vegan|veganistisch|vegetarian|vegetarisch)\b',q+' '+earlier,re.I):return self.inner.invoke(state)
        matches=[r for r in recipes if all(ingredient_in_record(r,t) for t in include) and not any(ingredient_in_record(r,t) for t in exclude)]
        if diet!='none':matches=[r for r in matches if diet in [str(x).casefold() for x in r.get('dietary_tags',[])]]
        if decision.intent=='alternative' or is_alternative:
            shown=' '.join(str(m.get('content','')).casefold() for m in history if m.get('role')=='assistant')
            matches=[r for r in matches if r['name']!=state.get('recipe_focus') and r['name'].casefold() not in shown]
        if not matches:
            return {'route':'retrieve','answer':'I could not find a recipe in the collection matching those ingredients and exclusions. What would you like to change?', 'calls':[],'recipe_focus':None,'safety':{'stage':'semantic_no_match','category':'allow'}}
        caveat=' The dietary label comes from the source; check ingredients and labels.' if diet!='none' else ''
        query=f"validated semantic lookup: include={','.join(sorted(include))}; exclude={','.join(sorted(exclude)) or '(none)'}; diet={diet}; intent={decision.intent}"
        if decision.intent=='list':
            answer='Here are matching recipes from the collection:\n\n'+'\n'.join(f"- {r['name']} (serves {r['servings']})" for r in matches)+caveat+'\n\nWhich one would you like?'
            return {'route':'retrieve','answer':answer,'context':[record(r) for r in matches],'search_query':query,'recipe_focus':None,'calls':[],'safety':{'stage':'semantic_catalogue','category':'allow'}}
        reviewed=[r for r in matches if r['name'] in STEPS]
        recipe=(reviewed or matches)[0]
        # Suggest a sourced recipe and let the user ask for details. This avoids
        # fabricating steps for records that have not been reviewed.
        answer=f"How about {recipe['name']}? The source recipe serves {recipe['servings']}.{caveat} Would you like the ingredients?"
        return {'route':'retrieve','answer':answer,'context':[record(recipe)],'search_query':query,'recipe_focus':recipe['name'],'calls':[],'safety':{'stage':'semantic_catalogue','category':'allow'}}
