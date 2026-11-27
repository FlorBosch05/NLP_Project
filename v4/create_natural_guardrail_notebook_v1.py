"""Build a readable, separate notebook from the preserved real test runs."""
import json
from pathlib import Path
import nbformat as nbf

root = Path(__file__).resolve().parent
results = root / 'results'
cells = []
def md(s): cells.append(nbf.v4.new_markdown_cell(s))
def read(name): return json.loads((results / name).read_text(encoding='utf-8'))
def conversations(title, name):
    data = read(name); rows = data.get('turns', []) if isinstance(data, dict) else data
    md(f'## {title}\n\nRaw evidence: [results/{name}](results/{name}). The original trace and timings are retained there.')
    last = None
    for row in rows:
        scenario = row.get('scenario')
        if scenario and scenario != last: md(f'### {scenario}'); last = scenario
        if 'question' in row:
            md('**User:** ' + str(row['question']) + '\n\n**Assistant:**\n\n' + str(row.get('answer')) + '\n\n'
               + f"Route: `{row.get('route')}`; focus: `{row.get('focus')}`; seconds: `{row.get('wall_seconds')}`; safety: `{row.get('safety')}`; issues: `{row.get('problems', [])}`.")
        else: md('Test record: `' + json.dumps(row, ensure_ascii=False) + '`')

md('''# Natural conversations, NeMo guardrails and context — separate v17 record

Date: 27 November 2026. Tested locally with Ollama `qwen2.5:7b`, Streamlit, the existing recipe collection and NeMo Guardrails. These are development tests, not a statistically representative or independently held-out benchmark. Every result includes the actual response; the raw files additionally preserve debug details. Model responses can vary.

## What changed and why

The v14 exploratory conversations revealed false safety refusals, invented or mistranslated ingredients, and an onion-free recommendation followed by an ingredient list containing spring onions. V15 improved focused recipe follow-ups, exact ingredient evidence and isolated unit conversions. V16 addressed the user's Dutch carrot and English onion examples, a false block of a source-based Bibimbap overview and a too-broad chat suppression rule. V17 adds a model-assisted search interpreter: Qwen interprets intent and explicit ingredients, the application checks them against the user's text and structured recipe records, filters explicit exclusions, and carries recent preferences across turns. A constrained retry of a rejected general explanation is allowed only after a fresh NeMo output check. Previous versions remain separate.

The explicit examples are not the entire solution: other wording, follow-ups, alternative suggestions, two ingredients, exclusions and named-recipe conflicts were tested. The interpreter is nonetheless imperfect: aliases and negation are limited, not every implicit preference is understood, and the conversation window is finite. Recipe matching verifies recorded ingredients, not cross-contact or complete dietary safety.

## Results and limitations

* The latest v17 ordinary-question sweep produced no safety refusal in 16 selected questions. This counts refusals, not factual accuracy or helpfulness; for example the greeting asks for more detail and the Dutch tomato recommendation is in English.
* Targeted context and paraphrase runs each passed 9/9 of their own checks; 12/12 focused guardrail tests and 11/11 selected safety regression turns passed. These questions informed development and are not an independent holdout.
* In an earlier paraphrase run, an alternative lost the original ingredient; another case experienced a 60-second NeMo timeout. Context handling was revised; a later isolated retry succeeded, but the cause of that intermittent timeout is unknown and it is not proven fixed. An earlier carrot paraphrase omitted the ingredient and an initial named-recipe conflict was incorrectly rejected; both are retained below.
* The v15 conversation file was recorded before its final Borscht preparation addition. The v17 example tests include the later source-based result.
* No new Ragas run was performed for v17. Safety checks and this small exploratory sample do not certify safety, accuracy or general understanding.
* Some source names appear with damaged character encoding (for example Bánh mì in a captured result); this remains a data/display quality issue.

## Guardrail trade-offs

| Choice | Benefit | Cost and risk |
| --- | --- | --- |
| NeMo input/output checks using local Qwen | Blocks selected harmful requests and drafts; no Groq quota for inference | Model decisions can be wrong or inconsistent; a timeout or unavailable safety check fails closed. The yes/no response cap limits long output but may also truncate an ambiguous response. |
| Exact reviewed egg/overview templates | Prevents specific incorrect blocks while retaining checks around arbitrary instructions | Narrow exceptions and source data need maintenance; not a general food-safety guarantee. Raw debug evidence can include unadapted source instructions. |
| Retry a rejected general explanation once, then re-check with NeMo | Can recover benign replies such as simmering versus boiling | Extra latency and model calls; retry is not fact checking and can still be rejected or hallucinate. |
| Carry recent safety context; permit standalone numeric conversion | Keeps anaphoric hazardous/allergy follow-ups guarded without blocking a separate unit conversion | Limited history can forget older context; vague follow-ups may be overblocked; ingredient records cannot establish allergy or cross-contact safety. |
| Qwen interpretation followed by source matching | Handles different wording and verifies explicit ingredients against records | Finite recent history, partial Dutch aliases, complex negation and implicit preferences can fail. Unsupported exclusions need clarification. Source records and dietary labels are not independently verified. |
| Local processing | No Groq key/quota needed for these tests | Local model and NeMo checks cost time and can time out. Existing model-call counters do not count all semantic-parser and NeMo calls. |

## Screenshots

The first is an actual v14 browser capture showing inaccurate Dutch ingredient translations; the second is an actual v16 browser capture after the Dutch carrot fix. V17 was tested separately using the real Streamlit test interface, as recorded below.

![v14 Dutch ingredient issue](results/screenshots_natural_v1/v14_dutch_failure.jpg)

![v16 Dutch carrot recipe](results/screenshots_natural_v1/v16_wortel.jpg)
''')

files = [
 ('Baseline v14: eight natural conversations', 'natural_nemo_conversations_v1_app_ollama_conversation_v14_20261127_104108_800300.json'),
 ('V15: same natural conversations', 'natural_nemo_conversations_v1_app_ollama_conversation_v15_20261127_104453_827700.json'),
 ('V15: user carrot/onion examples', 'user_carrot_onion_v1_app_ollama_conversation_v15_20261127_135221_824500.json'),
 ('V16: user carrot/onion examples', 'user_carrot_onion_v1_app_ollama_conversation_v16_20261127_135528_735600.json'),
 ('V17: user carrot/onion examples', 'user_carrot_onion_v1_app_ollama_conversation_v17_20261127_141222_337300.json'),
 ('V17: broader ordinary questions', 'benign_questions_v1_app_ollama_conversation_v17_20261127_141958_668500.json'),
 ('V17: paraphrase checks, earlier failure', 'semantic_holdout_v1_20261127_141127_048300.json'),
 ('V17: paraphrase checks, subsequent run', 'semantic_holdout_v1_20261127_141938_868400.json'),
 ('V17: context checks, earlier failure', 'semantic_context_v1_20261127_141517_283700.json'),
 ('V17: context checks, subsequent run', 'semantic_context_v1_20261127_141708_824400.json'),
 ('V17: earlier variant failures and timeout', 'semantic_variants_v1_20261127_140234_369000.json'),
 ('V17: isolated negative preference retry', 'negative_preference_v1_20261127_140834_430200.json'),
 ('V17: targeted ordinary checks', 'ordinary_nemo_v1_20261127_141811_726200.json'),
 ('V17: direct NeMo guardrail checks', 'nemo_rails_v5_20261127_140525_450300.json'),
 ('V17: selected safety regression conversations', 'safety_nemo_v4_20261127_142443_379900.json'),
]
for title, name in files:
    if (results / name).exists(): conversations(title, name)
md('''## Running v17

From the project root, with Ollama and `qwen2.5:7b` available:

```powershell
.\\v4\\.venv_nemo_v1\\Scripts\\python.exe -m streamlit run v4\\app_ollama_conversation_v17.py
```

Stop the older Streamlit process and open the new address; check the v4.17 label. This is the environment used in testing; it borrows packages from the project's base environment through a `.pth` file and is not a portable standalone installation. `OLLAMA_MODEL` overrides the default. Test scripts and timestamped JSON files in `v4` and `v4/results` make the checks reproducible, subject to model nondeterminism and local availability.
''')
nb = nbf.v4.new_notebook(cells=cells, metadata={'kernelspec': {'display_name':'Python 3','language':'python','name':'python3'}})
nbf.validate(nb)
out = root / '40_natural_conversations_guardrails_v1.ipynb'
nbf.write(nb, out)
print(out, len(cells), 'cells')
