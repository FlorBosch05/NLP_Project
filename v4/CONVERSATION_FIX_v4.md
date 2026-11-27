# Soup conversation: grounding and recipe focus

## Problem
The user reported that a request for soup was treated as chat, the assistant invented “Salted Tomato Soup” without retrieved evidence, a serving-count follow-up switched to unrelated recipes, and a correction received an inappropriate safety refusal. We reproduced the sequence with the earlier app and local Qwen; the saved baseline is `results/soup_conversation_v1_20261126_115129_071300.json`. Generated model output can vary between runs.

## What changed
`app_ollama_conversation_v4.py` wraps the prior agent in a separate `ConversationGraph` before the existing input/output safety checks. Broad supported soup recommendations are selected from stored V4 recipes and real retrieved context is attached. The selected recipe name is stored in the Streamlit conversation state; a serving question uses that specific recipe's stored serving count or asks which recipe is meant when there is no selection. Clearing conversation also clears the selection. A model-generated chat answer containing recipe/ingredient/instruction markers without retrieval is replaced with a request for more detail. This is a narrow safeguard, not an exhaustive grounding verifier.

When the user asks about tomato soup, the app identifies Gazpacho as a cold tomato soup in the collection, makes that distinction explicit, and asks if that is the recipe they want. It does not invent a hot tomato soup. Source dietary tags can be used for vegetarian/vegan filters but are not verified allergy claims. A small set of unsupported preferences results in a clarifying question. The safety classifier was given an explicit example allowing an ordinary serving question with an unspecified recipe; hazardous, allergy and override requests are still checked and blocked, and classifier failures still fail closed. The versioned safety and tortilla behavior remain in use.

This is targeted functionality. Recommendations use the first matching stored soup and a limited set of phrase rules; they do not rank taste, guarantee that a soup is salty or satisfy every preference. An unsupported preference may produce a generic question. Generated answers on other paths can still be wrong or ungrounded, and small-model safety checks can still overblock or miss problems. The user can inspect retrieved context in the UI; the locally sourced recipe data has not been independently kitchen-tested.

## Tests and iterations
- Earlier app: the reported four turns reproduced chat routing, invented Salted Tomato Soup, unrelated soup references and a safety refusal. `results/soup_conversation_v1_20261126_115129_071300.json`.
- First conversation fix: recommendation and serving tracking worked, but the safety output check blocked the second turn. `results/soup_conversation_v1_20261126_115243_556900.json`.
- Second iteration: the replay returned a grounded soup, a consistent serving count and a cold-Gazpacho correction. A separate no-recipe serving question then exposed an input-classifier false block. `results/conversation_regression_v1_20261126_115412_479800.json`.
- Current version: 17 UI turns passed in `results/conversation_regression_v4_20261126_224437_757000.json`, including the reported exchange, no-recipe clarification, named-recipe focus, ingredient follow-up, double-it scaling, an unsupported preference, hazards, conversion and tortilla. Checks are targeted; they do not prove every response is factually correct.
- The 11-turn safety regression passed: `results/safety_conversation_v1_20261126_224234_656400.json`. The 20-case agent diagnostic returned the expected routes 20/20 and six expected MCP outputs 6/6: `results/diagnostic_conversation_v1_20261126_224248_042400.json`. This is an existing development set, not a held-out benchmark or a new Ragas evaluation.

## Evidence and run
[Serving follow-up screenshot](results/screenshots_conversation_v1/01_soup_followup.jpg); [tomato correction screenshot](results/screenshots_conversation_v1/02_tomato_correction.jpg).

From `NLPproject`, start Ollama and run `.\.venv\Scripts\python.exe -m streamlit run v4\app_ollama_conversation_v4.py`. The `qwen2.5:7b` local model and cached embeddings must be available. This file is a separate version; older apps remain unchanged. The notebook's `%%writefile` cells reproduce the separate files when run from `v4` and will overwrite files with the same names.
