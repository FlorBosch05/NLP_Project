# Culinary safety rails — local Ollama version 2

## Objective and design
This separate version wraps the local V4 graph with input and output safety checks; earlier apps are unchanged. It uses project-specific rules and a local Ollama classifier, not NeMo Guardrails. The assignment names NeMo as an example; check with the instructor if that particular framework is mandatory. It is an experimental safety layer, not a certified food-safety or allergy service.

Before routing or MCP calls, explicit keyword rules flag examples of poisonous/non-food substances, allergy-related requests, and instructions to override safety rules. The local model classifies other requests as allow, allergy, hazard, injection or uncertain. A blocked question receives a fixed response rather than model-generated hazardous guidance. Up to eight recent messages are examined for allergy context, so follow-ups after a stated allergy remain conservative within that window. A model or parser failure results in an uncertainty response. Clear conversation resets history; allergy context is not a permanent user profile.

After the agent answers, an independent classifier checks the output and a separate expression catches certain categorical allergy assurances. Rejected output and retrieved context are withheld from the UI. The same local model is used for generation and classification, so errors and prompt-injection susceptibility can be correlated. The rules and classifier are not exhaustive, do not verify recipe ingredients, cannot determine individual allergy safety, and may block harmless requests or miss unsafe ones. Test findings are examples, not a safety guarantee. The global UI reminder still tells users to check source tags and cross-contact.

The safety classifier adds local inference calls and latency. The interface's existing model-call token totals exclude those classifier calls; total request time includes them. Calls are local; no Groq key is required.

## Live and failure tests, 26 November 2026
- `results/safety_ollama_v2_20261126_111559_565800.json`: 11 UI turns passed. These include English and Dutch bleach requests, raw chicken, allergy with a follow-up, a jailbreak, a disguised harmful request, a normal recipe and double-it follow-up, a conversion, and a vegan source tag.
- `results/safety_output_v2_20261126_111621_376700.json`: five checks passed: unsafe synthetic output, an allergy assurance, a normal conversion, classifier failure, and suppression of a rejected output/context.
- The first iteration, saved separately in `results/safety_ollama_v1_20261126_111518_808300.json`, overblocked a normal scaling response and a conversion. Version 2 revised the classifier instructions and passed those examples. This is one small test set; additional adversarial, multilingual, false-positive and regression testing is needed before relying on the layer.

## Run and reproduce
From `NLPproject`, start Ollama and run `.\.venv\Scripts\python.exe -m streamlit run v4\app_ollama_safety_v2.py`. The installed `qwen2.5:7b`, cached embeddings, and Ollama dependencies are required. Run `v4/test_safety_ollama_v2.py` and `v4/test_safety_output_v2.py` to save new test results. The cells below write the separate versioned files; execute from `v4` and avoid overwriting edited files accidentally.
