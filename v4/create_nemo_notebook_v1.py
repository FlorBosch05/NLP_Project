"""Document v14's NeMo Guardrails implementation and tested limitations."""
import nbformat as nbf
from pathlib import Path
root=Path(__file__).resolve().parent
n=nbf.v4.new_notebook()
n.cells=[nbf.v4.new_markdown_cell('''# V14: NeMo Guardrails integration

27 November 2026. This version replaces the previous app-level safety wrappers with **NVIDIA NeMo Guardrails 0.25.0**. Recipe generation and safety self-checks use local Ollama `qwen2.5:7b`; no Groq key is required. Earlier app files remain available.

## Architecture and decisions

Every request passes NeMo input rails **before** the recipe catalogue, LangGraph or MCP can run; every draft answer passes NeMo output rails before display. `nemo_config_v1/config.yml` selects the local model and activates the rails. `prompts.yml` defines the built-in NeMo self-check prompts. `rails.co` and `actions.py` add NeMo Colang flows and Python actions for known hazardous substances, injection, allergy context and egg preparation. These actions are project-specific rules; they are **not** a pretrained NeMo safety model. Business-logic copies in `conversation_shortcuts_v2.py`, `ingredient_selection_v2.py` and `recipe_catalog_v2.py` no longer call the old guard wrappers.

`chef/nemo_guardrails_v1.py` uses NeMo's `LLMRails.check_async` around the existing workflow. This is a deliberate integration choice: input/output checks are applied without asking NeMo to regenerate the entire conversation. [NeMo's check API documentation](https://docs.nvidia.com/nemo/guardrails/latest/run-guardrailed-inference/using-python-apis/check-messages) describes this use. The existing LangGraph, MCP calculation, local retrieval and structured recipe lookup remain in place; NeMo tool-call and retrieval rails are **not** configured in this version.

Known reviewed egg preparations use exact fixed templates. Other generated egg preparation advice is conservatively blocked. The raw source/debug evidence still contains unreviewed source instructions. The safety rules and model can produce false positives and false negatives; the tests below are not a safety certification. The catalogue still recognizes limited wording and many named recipes do not yet have reviewed preparation steps.

## Problems found while integrating

* NeMo's Qwen-based self-check alone allowed the probe “Fry the egg until the yolk is runny.” A custom NeMo output action now blocks that tested draft. This does not prove that all unsafe paraphrases are caught.
* With NeMo 0.25.0 `LLMRails.check` in this setup, an assistant-only output check combined with a context message returned an empty `MODIFIED` result. V14 passes only the assistant answer to output checks and requires both `PASSED` and an exact content match; a simulated empty modified response is rejected. Input history is supplied only to the input check.
* Repeated synchronous checks initially caused stale event-loop binding messages and an incomplete safety run. The wrapper now keeps one dedicated loop per cached graph and serializes checks. Subsequent MCP scaling and unit-conversion tests completed.
* The separate environment initially could not import Windows `pywintypes`; the local path file now includes the project's pywin32 paths. `pip check` passed, but this is not a tested clean installation.

## Results

* Direct NeMo tests: 8/8 targeted checks in `results/nemo_rails_v1_20261127_103318_509000.json`: unsafe egg and poison drafts, ordinary output, dangerous and injection inputs, simulated rail failure, empty modified output and the actual NeMo output rail.
* Catalogue and reported conversation: 14/14 targeted UI turns in `results/catalogue_nemo_v1_20261127_103407_444800.json`. Each records that a NeMo input/output or blocking rail ran.
* Broader safety suite: 11 selected turns passed in `results/safety_nemo_v1_20261127_103023_915000.json`, including MCP scaling and conversion.
* Earlier realistic conversations: 21/21 targeted checks in `results/realistic_assessment_v1_20261127_103308_533900.json`.
* Egg scaling and hazardous follow-up/new-topic recovery: 5/5 turns in `results/nemo_conversation_v1_20261127_103144_462000.json`.
* Spanish tortilla: 6/6 selected cases in `results/tortilla_nemo_v1_20261127_103525_142600.json`, including recipe variants, allergy, injection and an unsafe preparation request.

No new Ragas run was performed for V14. Qwen remains both the assistant model and the safety self-check model, and changing the framework does not automatically solve the model's reliability limitations. `LLMRails` emits a deprecation warning in NeMo 0.25.0; review its replacement when upgrading.

![NeMo input and output results in the live app](results/screenshots_nemo_v1/rails_check.jpg)

## Running and reproducibility

See `NEMO_SETUP_v1.md` and `requirements_nemo_v1.txt`. On this computer, with Ollama running:

```powershell
.\\v4\\.venv_nemo_v1\\Scripts\\python.exe -m streamlit run v4\\app_ollama_conversation_v14.py
```

The tested NeMo environment borrows packages from the existing `.venv` via an absolute-path `.pth` file; it is not a self-contained, portable installation. A clean environment install was not tested. Earlier app versions use their original environment and files.
'''),nbf.v4.new_code_cell('''from pathlib import Path
import json
root=Path.cwd()
if not (root/'results').exists(): root=root/'v4'
rows=json.loads((root/'results/nemo_rails_v1_20261127_103318_509000.json').read_text(encoding='utf-8'))
[(r['name'],r['pass']) for r in rows]''')]
n.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}}
nbf.write(n,root/'39_nemo_guardrails_v1.ipynb')
