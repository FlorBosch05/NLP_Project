# Flavor Chef V4: sourced recipes

This separate version replaces the synthetic V3 corpus with 36 recipes selected from the published UniTools World Recipes dataset. The selection covers 16 country labels. The data was downloaded from the publisher's JSON dataset; no websites were scraped. This is a convenience sample, not a representative sample or a safety certification.

**Attribution:** Recipe data: [UniTools — theunitools.com](https://theunitools.com/en/data), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Adaptations: selected 36 records; retained English fields, source ingredient quantities, units, notes and scaling labels; combined recipe steps and source durations into text; omitted Russian fields, photos and nutrition. The adapted recipe data is shared under CC BY-SA 4.0. Code is separate from the recipe-data licence. The publisher's dataset does not provide live individual recipe URLs in version 2.0.0; the project records the dataset link, version, selected slugs and source SHA-256 in `data/source_manifest_v4.json`.

## Run

From `NLPproject`, use the existing virtual environment and the API key/model in `NLPproject/.env`:

```powershell
.\.venv\Scripts\python.exe -m streamlit run v4\app.py
```

V4 builds its own local Chroma index and does not overwrite previous versions. Model calls use the configured Groq quota. Version 4 is not yet tested end-to-end with a live model or evaluated with Ragas; the earlier V3 scores belong to a different corpus and cannot be reused. The current app model stays as configured in `.env`.

## Data and safety

The publisher supplies ingredient quantities, instructions, prep/cook minutes, serving counts and dietary tags. They have been checked for required fields and preserved against the downloaded source; they have not been independently verified or kitchen-tested by this project. An empty tag list means the publisher supplied no tag, not that a dish fails or satisfies a diet. Check product labels and cross-contact; do not treat tags as allergy guarantees. Some dishes or substitutions can require additional food-safety review. Source durations are publisher values, not measured by this project.

## Serving scaling

Ingredients marked `linear` are multiplied by the serving ratio; numeric `fixed` ingredients stay fixed. The source uses `damped` for some seasonings but does not give a formula in the dataset, so V4 explicitly reports them for manual adjustment rather than inventing an amount. Ingredients without numeric quantities stay unspecified. Unit conversion only works within mass or within volume; converting grams to cups requires ingredient density. The calculation is deterministic, but the model can still select the wrong recipe or serving count.

In the first Qwen live test, the calculated ingredient quantities were correct but the model repeated source instructions containing original quantities as though they belonged to the scaled recipe. The separate `app_scale_v2.py` and `chef/agent_scale_v2.py` address this by presenting the deterministic tool result and warning that source instructions and timings have not been scaled. An offline graph/MCP test passes; a live retest is still needed. The original app and its test results remain untouched.

## Tests and notebooks

`test_source_v4.py` validates the data structure and exercises the real MCP server and LangGraph scaling path with a test model, without Groq. `check_retrieval_v4.py` performs a 13-question local retrieval check. Its expected-section labels were generated for this project; it is not Ragas. The numbered notebooks contain the corresponding runnable source and explanations. Open JupyterLab from `v4`; the `%%writefile` cells regenerate runtime files, so use a new filename or version if making revisions.

`ingest_source_v4.py` can regenerate the selection from the publisher's original JSON: it checks the source hash recorded in the manifest and refuses to overwrite an existing output. Use `--input PATH` for a previously downloaded source and `--output NEW_FILE`. Its original source dataset is available at `https://theunitools.com/data/unitools-recipes-v1.json` and may change, so a changed hash needs review rather than silent reuse.

The project includes `data/evaluation_v4.json` with 20 source-derived cases. Its expected answers and dietary interpretations still require independent human review. Separate `evaluate_qwen_v1.py` and `score_qwen_v1.py` run the Qwen experiment without changing `.env`; they consume Groq quota. The latter records reported judge usage where available. A source-data change invalidates earlier benchmark comparisons. See `QUALITY_NOTES_v4.md` and `QWEN_EVALUATION_v1.md` for results and limitations.
