# Readable sources and raw debugging trace

## Change
`app_ollama_conversation_v9.py` is a separate interface version of the earlier v8 app. Each assistant response has two panels:

- **Sources and measurements** presents recipe names, readable ingredient amounts and notes, source sections, the UniTools dataset link, any calculation summary and available timing/token measurements. Stored recipe records and search results have different labels. Structured records are shown first for readability; search results retain their relative order.
- **Debug: complete raw trace** displays the complete unchanged data structure, including the original chunk order, scores, tool arguments and telemetry. It remains available for troubleshooting.

If no source was used, the panel says so. An absent token count is labelled unavailable, not zero. Counts exclude safety-classifier calls. The display uses the existing graph, evidence records and safety layer. It does not re-evaluate the Ragas scores or assert that source recipes and dietary tags are independently verified.

## Tests
The two-turn live UI test checked source attribution, ingredient amounts, clear provenance, structured evidence equality against the stored recipe, the full raw trace, and rendering again after a follow-up: `results/source_display_test_v2_20261126_231621_023300.json`. The 11-turn live safety regression passed before the display-only ordering adjustment: `results/safety_display_v1_20261126_231504_840300.json`. After the ordering change, the two-turn source and raw-trace check was rerun and passed. The browser layout was checked and screenshots were saved.

[Readable source panel](results/screenshots_source_display_v1/01_readable_sources.jpg) · [Raw debug trace](results/screenshots_source_display_v1/02_raw_debug.jpg).

## Run
From `NLPproject` with Ollama and cached local embeddings available: `.\.venv\Scripts\python.exe -m streamlit run v4\app_ollama_conversation_v9.py`. The previous v8 file remains available. Run the notebook writefile cells from `v4`; they overwrite files with the same names.
