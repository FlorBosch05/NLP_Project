# Flavor Chef V4.14 — NeMo Guardrails

The app entry point is `app_ollama_conversation_v14.py`. It wraps the recipe and MCP workflow with NVIDIA NeMo Guardrails 0.25.0 input and output rails. NeMo's self-check rails use local Ollama `qwen2.5:7b` by default; the project's custom food-safety checks run as NeMo actions. Qwen remains the recipe assistant too. No Groq key is needed for this version.

## Start the tested environment on this machine

Start Ollama and make `qwen2.5:7b` available. From `NLPproject` run:

```powershell
.\v4\.venv_nemo_v1\Scripts\python.exe -m streamlit run v4\app_ollama_conversation_v14.py
```

Stop any old Streamlit app or use a different port. Verify the page says `Version 4.14 · NeMo Guardrails`.

The tested NeMo environment is separate, but it **borrows the existing project's `.venv` packages** through `v4/.venv_nemo_v1/Lib/site-packages/flavor_chef_base_v1.pth`. That file contains absolute paths, including the Windows pywin32 paths needed for MCP. Moving or deleting the project or its original `.venv` will break this particular environment until it is rebuilt. The original environment was not modified by the NeMo installation.

For a fresh independent environment, `requirements_nemo_v1.txt` lists the base dependencies, `langchain-ollama`, and pinned NeMo 0.25.0. A clean install was **not** tested in this run; dependency resolution and model downloads may vary. One possible setup from the project directory is:

```powershell
.\.venv\Scripts\python.exe -m venv v4\.venv_nemo_clean_v1
.\v4\.venv_nemo_clean_v1\Scripts\python.exe -m pip install -r v4\requirements_nemo_v1.txt
.\v4\.venv_nemo_clean_v1\Scripts\python.exe -m streamlit run v4\app_ollama_conversation_v14.py
```

## Where the rules live

- `nemo_config_v1/config.yml`: enables the NeMo input and output flows and selects the local Ollama backend.
- `nemo_config_v1/prompts.yml`: prompts for the NeMo self-check input/output rails.
- `nemo_config_v1/rails.co` and `actions.py`: Colang flows and project-specific checks for allergies, poison, injection and egg cooking.
- `chef/nemo_guardrails_v1.py`: runs the NeMo checks before and after the entire application workflow; failures close the request. It reuses a dedicated asynchronous loop and accepts an output only when the check reports a pass and the checked content exactly matches the draft.

The structured recipe shortcuts are separate from the safety layer; they no longer call the previous custom guard implementation. Some safety rules are still custom **NeMo actions**, not pretrained NeMo safety models. The custom egg rule allows only exact, predefined reviewed egg-cooking answers. Qwen and keyword rules can both make mistakes; the tested cases do not prove general safety. The raw trace may contain unreviewed original recipe source instructions.

NeMo 0.25.0 emits a deprecation warning for its `LLMRails` engine. That engine is used because the configuration includes custom Colang actions; reassess compatibility when upgrading. The app uses input/output checks only, not NeMo tool-call or retrieval rails.
