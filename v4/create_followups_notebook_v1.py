"""Preserve the user report and the actual v18 experiment transcripts."""
import json
from pathlib import Path
import nbformat as nbf
root=Path(__file__).resolve().parent
cells=[]
def md(text):cells.append(nbf.v4.new_markdown_cell(text))
md('''# V18: conversational follow-ups and pantry requests

27 November 2026. This separate version responds to the user's report that an egg suggestion followed by “yes do mar” was refused, “I have salt and tomato what food can I make” asked for an ingredient again, and “yes please what is the recipe” repeated an incomplete recipe.

## Change and rationale

* An affirmative refers to an explicitly offered ingredient list only when there is a current source-backed recipe focus and the immediately preceding assistant answer offers ingredients. The list is built from the recipe record. An ambiguous “yes” without a focus does not invent a recipe.
* A request for the focused recipe uses the existing named recipe path, with reviewed preparation when available and an explicit limitation when it is not. A different named recipe is not silently replaced by the focus.
* For a clear pantry request, the ingredient interpreter preserves the actual mentioned candidate ingredients even if the model omits one; the records are checked for all requested items. The suggestion says it needs other ingredients. A request for fresh tomato is not silently satisfied by tomato paste.
* NeMo still checks the original input and resulting answer; the routing changes do not disable or exempt safety checks. Actual NeMo decisions can be inconsistent, and allergy and food-safety risks cannot be established from source ingredients alone.

## Trade-offs and limits

The short-affirmation recognizer is deliberately limited to familiar English/Dutch forms, and only after an explicit offer; it will not understand every phrase. Pantry intent still depends partly on Qwen and a limited vocabulary, and the record matcher does not establish that a recipe uses *only* the supplied items. Stored ingredients may be incomplete, labels are not independently validated and source names may have encoding defects. When reviewed preparation is unavailable, the app says so rather than fabricating it. Local Qwen and NeMo add latency, can refuse benign requests, and can time out. The recent history window is finite. These tests are development checks, not evidence of general language understanding or comprehensive safety, and no new Ragas run was performed.

The final selected run passed all 16 conversation turns, the focused routing checks passed 4/4, and the selected safety run passed 11/11. These counts are specific assertions, not independent accuracy measurements. The browser screenshot below shows the actual v18 egg follow-up.

![V18 egg follow-up](results/screenshots_natural_v1/v18_egg_followup.png)

## Reported V17 exchange

The user reported an egg suggestion followed by “yes do mar” leading to “I cannot safely assess this request or response”; after the user requested Menemen by name it showed the recipe. The separate pantry exchange asked for an ingredient despite “salt and tomato” being supplied; its follow-up returned partial Lomo saltado and then repeated the same partial answer while reporting missing tool data. This is a user-provided transcript, not a newly replayed V17 execution.

## Earlier V18 exploratory test and a newly found problem

The first v18 run passed its then-current assertions, but manual inspection found that a request for carrots and tomatoes selected Borscht and then Mercimek çorbası, whose records list **tomato paste** rather than fresh tomato. That check was missing from the first test. The next iteration adds a distinction for pantry requests, plus a regression check; both actual runs are preserved below.
''')
for pattern,title in [('followups_v18_v1_20261127_143916_921200.json','First v18 run'),('followups_v18_v1_*.json','Additional v18 run'),('safety_nemo_v5_*.json','V18 safety regression')]:
 files=[root/'results'/pattern] if '*' not in pattern else sorted((root/'results').glob(pattern),key=lambda p:p.stat().st_mtime)
 if '*' in pattern and files:files=[files[-1]]
 for path in files:
  if not path.exists():continue
  data=json.loads(path.read_text(encoding='utf-8')); rows=data.get('turns',[]) if isinstance(data,dict) else data
  md(f'## {title}\n\n[Raw trace: {path.name}](results/{path.name})')
  for row in rows:
   if 'question' not in row:md('Test error: `'+str(row)+'`');continue
   d=row.get('details') or {}; md('### '+str(row.get('scenario',''))+'\n\n**User:** '+str(row['question'])+'\n\n**Assistant:**\n\n'+str(row.get('answer'))+'\n\nRoute: `'+str(row.get('route',d.get('route')))+'`; focus: `'+str(row.get('focus',d.get('focus')))+'`; safety: `'+str(row.get('safety',d.get('safety')))+'`; issues: `'+str(row.get('problems',[]))+'`')
md('''## Run locally

```powershell
.\\v4\\.venv_nemo_v1\\Scripts\\python.exe -m streamlit run v4\\app_ollama_conversation_v18.py
```

The tested environment relies on the existing project base environment; Ollama with `qwen2.5:7b` must be available. Stop the previous app first and check the version displayed in the interface. `test_followups_v18_v1.py`, `test_followup_routing_v1.py` and `test_safety_nemo_v5.py` contain the checks; timestamped result files preserve actual outputs, routes and traces.
''')
nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}})
nbf.validate(nb);out=root/'41_followups_pantry_v1.ipynb';nbf.write(nb,out);print(out, len(cells),'cells')
