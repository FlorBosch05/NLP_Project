"""Record the reported conversation and the v11 safety trade-off."""
import nbformat as nbf
from pathlib import Path
root=Path(__file__).resolve().parent
n=nbf.v4.new_notebook()
n.cells=[nbf.v4.new_markdown_cell('''# V11: false safety refusals in recipe chat

27 November 2026. The user's six-message conversation was reproduced against v10. Spaghetti, the onion-soup follow-ups and the carrot request were rejected by the *output* classifier as `uncertain`. A separate probe confirmed that Qwen actually returned that category for a normal onion-soup draft; the visible trace alone does not prove why the model chose it. The replay is saved in `results/user_chat_v1_app_ollama_conversation_v10_20261127_094822_727100.json`.

## What changed and why

`app_ollama_conversation_v11.py` is a separate app. `conversation_shortcuts_v1.py` recognizes narrowly defined, complete simple requests: a misspelling of spaghetti, a misspelled onion-soup confirmation, and the specified pattern for a recipe containing an ingredient in the stored corpus. It checks the original input safety layer first. It responds with a fixed message or a list derived from the stored record; it does not use a generative model to invent the recipe. The collection has no spaghetti recipe, so it says so. For Borscht and French onion soup, the preparation text is a fixed adaptation of the source and can be returned on the initial request or a short follow-up.

`safety_rails_v9.py` retains the input safety checks and the output classifier for general answers. It exempts only answers that exactly match the existing structured ingredient-list template, preventing that controlled list from being falsely blocked. The new shortcut path likewise skips the output-model check only for its fixed/source-derived replies; it does not skip the input check. This is a deliberate safety/usability trade-off, not a claim that the classifier or all recipes are safe. These shortcuts cover limited wording and only two reviewed sets of cooking steps; other answers may still be falsely refused. The input classifier remains capable of false refusals. A model or parsing failure remains fail-closed.

## Results

* Six user messages replayed successfully with v11, saved in `results/user_chat_v1_app_ollama_conversation_v11_20261127_095232_965800.json`. Spaghetti is absent; onion soup and Borscht include ingredients and preparation.
* Follow-up preparation, allergy history, a bleach request and a jailbreak-style soup request were exercised in `results/shortcuts_v1_20261127_095248_538000.json`. Allergy and hazardous examples remained blocked. This was recorded before the subsequent narrowly scoped ingredient-template guard adjustment; the dedicated safety and conversation suites were rerun after that adjustment.
* Final v11 safety suite: 11 selected turns passed in `results/safety_final_v2_20261127_095337_450800.json`.
* Final v11 realistic conversation suite: 21/21 targeted checks passed in `results/realistic_assessment_v1_20261127_095346_963700.json`. An earlier run failed the Gazpacho ingredient follow-up and is preserved in `results/realistic_assessment_v1_20261127_095219_810100.json`.

Tests are examples, not proof of safety. The earlier Dutch translation issue and generic refusals for zero servings and mass-to-volume conversions remain open. No new Ragas evaluation or browser screenshot was produced for v11.

## Run

Start Ollama with `qwen2.5:7b` available and, from the project folder, run:

```powershell
.\\.venv\\Scripts\\python.exe -m streamlit run v4\\app_ollama_conversation_v11.py
```

The previous app remains in `app_ollama_conversation_v10.py`. Existing tabs may still be running that version and need to be restarted to use v11.
'''),nbf.v4.new_code_cell('''from pathlib import Path
import json
root = Path.cwd()
if not (root / 'results').exists(): root = root / 'v4'
result = json.loads((root / 'results/user_chat_v1_app_ollama_conversation_v11_20261127_095232_965800.json').read_text(encoding='utf-8'))
[(turn['question'], turn['answer']) for turn in result]''')]
n.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}}
nbf.write(n,root/'36_safety_chat_fix_v1.ipynb')
