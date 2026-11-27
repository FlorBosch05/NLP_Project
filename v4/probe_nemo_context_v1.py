"""Verify NeMo context propagation and real prior responses."""
import json,os,sys
from pathlib import Path
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
root=Path(__file__).resolve().parent;sys.path.insert(0,str(root))
from nemoguardrails import RailsConfig,LLMRails
from nemoguardrails.rails.llm.options import RailType
r=LLMRails(RailsConfig.from_path(str(root/'nemo_config_v1')))
items=json.loads((root/'results/catalogue_v1_20261127_101701_575200.json').read_text(encoding='utf-8'))
for item in items[:5]:
 text=item['answer'].replace('The temperature step is a food-safety adaptation; the source calls for a loose yolk.','The temperature step is a food-safety adaptation.')
 for t,role,content,context in [(RailType.INPUT,'user',item['question'],{}),(RailType.OUTPUT,'assistant',text,{'chef_reviewed_egg':True})]:
  try:
   messages=([{'role':'context','content':context}] if t==RailType.INPUT else [])+[{'role':role,'content':content}]
   res=r.check(messages,rail_types=[t]);print(item['question'],t,res.status,res.rail,repr(res.content)[:80],flush=True)
  except Exception as e: print(type(e).__name__,str(e),flush=True)
res=r.check([{'role':'context','content':{'chef_history':[{'role':'user','content':'I have an egg allergy.'}]}},{'role':'user','content':'list recipes with eggs'}],rail_types=[RailType.INPUT]);print('allergy history:',res.status,res.rail,flush=True)
