# Spanish tortilla safety and response fix

## Problem and investigation
In the prior safety-v3 diagnostic, the question “How does the source say to prepare Spanish tortilla?” was blocked by the output classifier as uncertain. The UniTools source describes a slightly loose egg centre. A separate reproduction produced a draft containing that suggestion which the same local classifier allowed; this shows that its decisions can vary and the old check was not sufficient to establish food safety. The earlier block's exact cause was not recorded, so it is not established that the loose-centre text caused that block. `results/tortilla_diagnosis_v1_20261126_113912_949700.json` is a diagnostic draft, not a verified safe recipe.

## Change and rationale
`app_ollama_safety_v5.py` uses `chef/safety_rails_v5.py`, a separate version. After the input safety check and retrieval, a small set of explicitly matched Spanish-tortilla preparation requests receives a concise fixed adaptation of the stored UniTools recipe. It advises cooking the centre to **71°C (160°F)** and measuring with a food thermometer, and labels this as a safety adaptation. [FoodSafety.gov's egg-dish temperature chart](https://www.foodsafety.gov/food-safety-charts/safe-minimum-internal-temperatures) supplies the guidance. The recipe is attributed to UniTools, CC BY-SA 4.0. This changes the source's suggested finish; it does not claim the source itself gives this temperature. The original source instructions are still visible as retrieved context and should not be mistaken for the adaptation.

The reviewed text still passes through the local output safety classifier; an unsafe/allergy question is checked before retrieval and the template. An output rejection or classifier failure still blocks the answer. The discarded model draft is never shown as the final answer, and its time to first token is not attributed to the displayed template. These are narrow supported phrasings, not a universal food-safety guarantee: other wording follows the ordinary model and guard, which can still err or block a safe request. The recipe and source tags are not independently kitchen-tested.

## Iterations and test results
The first candidate (`safety_rails_v4.py`) included a longer explanation of the loose centre and was blocked as hazardous by the output classifier in all three ordinary tortilla UI tests. The allergy, unsafe-egg and jailbreak cases passed. The shortened v5 adaptation avoids repeating the risky finish as a cooking instruction and keeps the explicit temperature check; it passed the same classifier. V4 and its failed results remain available at `results/tortilla_live_v1_20261126_114032_834400.json`.

- Six live UI cases passed: the original question, two paraphrases, and three blocked requests involving egg allergy, unsafe raw eggs or an instruction override. `results/tortilla_live_v2_20261126_114212_840700.json`.
- The prior 11-turn safety UI regression passed, covering ordinary recipe questions, scaling, conversions, hazards, allergy context and jailbreak examples. `results/safety_ollama_v5_20261126_114304_181900.json`.
- The existing 20-case diagnostic returned the expected route for 20/20 and exact MCP outputs for all 6 tool cases. This checks routing and exact tool outputs, not whether every generated answer is correct. It is a development set and the fix was targeted at one of its cases, not an independent holdout. `results/diagnostic_ollama_v1_20261126_114230_314700.json`.
- The previous Ragas results belong to the prior run; Ragas was not rerun on this version. Safety classifiers can give false positives or false negatives and need broader evaluation.

## Screenshots
- [Before: the source question was blocked](results/screenshots_diagnostic_v1/06_v3_tortilla_block_unresolved.jpg).
- [After: the app returns an adapted recipe with a temperature check](results/screenshots_tortilla_v1/01_tortilla_fixed.jpg).
- [After: the egg-allergy question is still blocked](results/screenshots_tortilla_v1/02_allergy_block.jpg).

## Run
From `NLPproject`: `.\.venv\Scripts\python.exe -m streamlit run v4\app_ollama_safety_v5.py`. Ollama, `qwen2.5:7b`, cached embeddings and the Ollama dependencies are required. The separate notebook `29_tortilla_fix_v1.ipynb` documents and regenerates the versioned code. Run its writefile cells from `v4`, and avoid overwriting changes unintentionally.
