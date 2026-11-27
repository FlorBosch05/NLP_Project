# Flavor Chef — MVP version 2

This version is separate from the original files in `NLPproject`. It contains a local Streamlit interface, a LangGraph workflow, recipe retrieval with LlamaIndex and Chroma, and an MCP server that performs exact scaling and supported unit conversions.

## Run

Use the existing environment and `NLPproject/.env`, which must contain `GROQ_API_KEY` and preferably `GROQ_MODEL=openai/gpt-oss-20b`. From the `NLPproject` directory:

```powershell
.\.venv\Scripts\python.exe -m streamlit run v2\app.py
```

If the environment has not been installed, follow the original `requirements.txt` setup. The first index build downloads a sentence-transformer model and may take several minutes. Later starts reuse a local Chroma collection. A collection name includes a fingerprint of the data, chunking strategy and embedding model. The interface lets you choose section or full-recipe chunks and top-k; switching strategies may trigger a new build.

## Notebooks

The numbered notebooks contain the implementation and explain its design choices. Open JupyterLab in the `v2` directory. Their `%%writefile` cells generate the matching runtime files; Streamlit and the MCP server need these files as executable modules. The original version stays in its original location.

To check the dataset, chunking and deterministic MCP tools without making model requests, run `.\.venv\Scripts\python.exe v2\test_mvp.py` from `NLPproject`.

## Data and safety

The corpus has 30 synthetic teaching recipes, each with ingredients, steps, two servings, an estimated cooking time and an ingredient-based dietary tag. They have not been cooked or independently validated. Times are illustrative estimates; ingredient labels and cross-contact require independent checks. The system should not be relied on for allergy or food-safety decisions. Substitutions are deliberately not supplied as corpus facts: when a reference is missing, the assistant should say so. No claim of independently verified ground truth is made.

## Architecture

The router uses the current request and recent chat history to select chat, recipe retrieval, serving scaling, or unit conversion. Retrieval uses a query rewritten as a standalone request. Scaling first searches the recipe collection; the LLM extracts known values and the MCP server validates and calculates them. Unit conversion supports g, kg, mg, ml, l, tsp and tbsp within a dimension. Conversion between mass and volume requires ingredient density and is rejected. The final model call uses the retrieved evidence and tool result. Requests and retrieved context are sent to Groq, so do not use private data unless that is appropriate for the account.

The UI displays the route, retrieved fragments and scores, tool arguments and results, model token counts where supplied, per-step timings, total time and time to first non-empty output token from the final streamed model call. The complete answer is displayed after generation; TTFT is measured, not shown as live streaming. Total token counts are reported as unavailable if a model call omits usage data. They do not include embedding computation or Ragas judge usage. Total time includes first-load indexing when applicable.

## Evaluation

`data/evaluation_v2.json` contains 20 manually authored reference cases: 13 recipe/retrieval cases, four unit conversions, two scaling cases and a greeting. References are derived from the synthetic corpus and have not had independent review. Ragas precision, recall and faithfulness are computed only on retrieval cases with retrieved context; routes and tool outputs are logged for all cases. Ragas uses an LLM judge and can be wrong or yield missing scores. No benchmark verifies real-world recipe safety.

From `NLPproject`:

```powershell
.\.venv\Scripts\python.exe v2\evaluate.py --strategy sections --top-k 5
.\.venv\Scripts\python.exe v2\evaluate.py --strategy recipe --top-k 5
```

Each run saves a new timestamped JSON file in `v2/results` with references, answers, chunks, routes, tool outputs, model-call telemetry and per-case Ragas scores. `--limit 1` runs a smoke test; `--no-ragas` skips judge calls. Full scoring uses Groq quota and may be slow or hit rate limits. For a long evaluation, first use `--no-ragas`, then score its saved JSON in small batches without repeating the original questions:

```powershell
.\.venv\Scripts\python.exe v2\score_saved.py v2\results\YOUR_RUN.json --offset 0 --limit 1
.\.venv\Scripts\python.exe v2\score_saved.py v2\results\YOUR_RUN.json --offset 1 --limit 1
```

Each batch creates a new result file and saves after each question. The offset counts only retrieval cases. Increase it until all 13 retrieval cases are covered; retry missing or failed scores separately. Compare strategies on the same fixed questions and inspect individual cases rather than trusting an average alone. See `RESULTS_NOTES.md` for the actual checks and remaining issues.

## Known limitations

The router and argument extractor are probabilistic; inspect the recorded route and tool inputs. The model may still make mistakes despite the grounding prompt. Conversation history is limited to the latest eight messages and is not persistent between app sessions. Ingredient quantities are rounded to three decimal places when scaled. Retrieval evaluation and recipe data need independent human validation. This MVP does not implement the extra-credit extensions.
