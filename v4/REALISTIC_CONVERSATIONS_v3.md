# Realistic conversations: test and iteration

## Scope
On 26 November 2026, seven fresh, project-authored multi-turn conversations were run through the local Streamlit app with Ollama `qwen2.5:7b`. They cover vegetarian soup and ingredient/scaling follow-ups; rejecting onions and asking for another soup; switching Guacamole to Borscht; tomato soup and scaling to eight; a meat-free soup and beef-stock question; unspecified-recipe clarification; and an egg allergy with a follow-up. These are development cases, not an independent held-out benchmark.

## Failures and changes
- In the original run the app repeated French onion soup after the user said they disliked onions. The revised version recognizes selected onion-exclusion phrases, checks stored ingredient names, and excludes the current recipe when another one is requested. The test selected Tom yum goong; the stored ingredient list contains no onion. It checks names, not product labels, cross-contact, synonyms or every possible wording.
- “Actually, tell me about Borscht instead” lost the recipe focus and was treated as general chat. The new version gives the named recipe's source overview and serving count, and retains that recipe for the follow-up.
- “What are its ingredients?” with no known recipe returned mixed context from several recipes. It now asks which recipe is meant. When one is selected, ingredient names and quantities are formatted from the stored record and associated with retrieved context; no quantity is invented when absent.
- “Can I make it for eight people?” did not consistently reach scaling. When a recipe is focused and the user uses the supported pattern, the requested count is passed to the existing MCP scaling workflow. Other wordings still rely on the model and are not guaranteed.
- A request for a meat-free soup and a subsequent beef-stock question were falsely blocked by the local safety classifier. The revised version uses a source vegan tag as a conservative data filter, identifies that tag as source-provided, and clarifies in the classifier prompt that a meat-free preference alone is not an allergy. An ingredient-presence answer refers only to what the source lists and advises checking labels. It is not an allergy or cross-contact guarantee.
- An intermediate iteration incorrectly blocked a harmless spicy-soup request when it explained the data could not be filtered. The final version says the collection does not label soup by spiciness and asks whether the user wants a suggestion. This is a limitation: it does not automatically rank spiciness or every dietary preference.
- The first exploratory runner also hit a Windows console encoding error on a Turkish recipe name. The revised runner escapes non-ASCII console output while retaining Unicode in saved results.

## Verification
- The final run recorded 19 turns across seven conversations: `results/realistic_conversations_v4_20261126_225223_376300.json`. The separate assessment checked 21 expected properties against the stored recipes and recorded 21/21 passes: `results/realistic_assessment_v1_20261126_225251_181900.json`. Those checks are selected assertions, not a full manual audit or proof that all replies are correct.
- The earlier 17-turn conversation regression passed: `results/conversation_regression_v6_20261126_225218_517100.json`.
- The 11-turn safety regression passed, including allergy, unsafe food and jailbreak examples: `results/safety_conversation_v3_20261126_225319_542700.json`.
- The 20-case existing diagnostic returned 20/20 expected routes and 6/6 exact expected MCP outputs: `results/diagnostic_conversation_v3_20261126_225338_066400.json`. This is a development set, not a new Ragas evaluation or a measure of all answer quality.
- Failed attempts remain in `results/realistic_conversations_v1_20261126_224658_161700.json`, `results/realistic_conversations_v2_20261126_224858_823100.json`, and `results/conversation_regression_v5_20261126_225125_119000.json`. The initial run ended one vegetarian scenario early because of console encoding, so its missing turns are not treated as failures or passes.

## Limitations and screenshots
Recognized preferences and exclusions are deliberately narrow and inferred from at most the recent conversation; the app cannot reliably infer every dietary condition, every ingredient synonym or a safe substitution. The source tags and ingredients are not independently kitchen-tested. The output classifier can still produce false positives or false negatives, and other paths can hallucinate. Clear conversation resets the recipe focus. New Ragas scores were not produced for this version.

[Alternative after rejecting onions](results/screenshots_realistic_v1/01_onion_alternative.jpg) and [correct follow-up serving count](results/screenshots_realistic_v1/02_followup.jpg) are actual captures of the final app.

## Run
From `NLPproject` with Ollama and the existing local model and embeddings available: `.\.venv\Scripts\python.exe -m streamlit run v4\app_ollama_conversation_v7.py`. The earlier versions remain separate. The notebook's writefile cells reproduce these files from `v4` and overwrite files with matching names.
