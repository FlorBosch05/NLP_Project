# Flavor Chef version 3

Version 3 keeps version 2 intact and adds a review of the synthetic corpus, explicit untested substitution suggestions for three recipes, and a labelled retrieval comparison. It remains a teaching prototype, not a validated cookbook or a food-safety service.

## Run

Use the existing `.venv` and the API key and model in `NLPproject/.env`. From the `NLPproject` directory:

```powershell
.\.venv\Scripts\python.exe -m streamlit run v3\app.py
```

The first run builds new V3 Chroma collections; V2 collections and files are not overwritten. The interface lets you select section or full-recipe retrieval and change top-k. Its example recipes and substitution suggestions are synthetic and have not been kitchen-tested. Cooking times are unverified estimates. Never infer allergy safety solely from its output.

## Documents and notebooks

See `DATA_REVIEW_v3.md` for the review scope, changes, safety sources and remaining gaps. `RETRIEVAL_RESULTS_v3.md` describes the experiment and its limitations, and `RESULTS_NOTES_v3.md` tracks the evaluation and quota interruptions. The numbered V3 notebooks explain and reproduce each component; run them from the `v3` directory. Their `%%writefile` cells create the matching runtime files. Existing V2 notebooks and comparison notebooks remain available separately.

## Reproduce local checks

```powershell
.\.venv\Scripts\python.exe v3\test_mvp.py
.\.venv\Scripts\python.exe v3\audit_data.py
.\.venv\Scripts\python.exe v3\compare_retrieval.py
```

The data audit is in `audit_data.py` and creates a new timestamped result on each run. These checks do not verify food safety, human ground truth or Ragas metrics. The retrieval comparison uses 13 named-recipe questions, top-k 5 and manually labelled expected sections. Its context-size estimate uses the embedding model tokenizer, not the Groq tokenizer or billable usage.

## Ragas

Run the V3 evaluation with `.\.venv\Scripts\python.exe v3\evaluate.py --strategy sections --top-k 5`. For quota-constrained accounts, add `--no-ragas` first, then score its saved results with `v3\score_saved.py` in small batches. If the evaluation stops because the daily token quota is exhausted, wait for quota recovery and resume the unattempted cases with `--offset N`, where N is the number already attempted, including the failed case only after you separately retry it. Every partial run is stored separately. The scorer records the judge model, and results are versioned by filename. Use the same judge and same V3 reference set to compare the two chunking approaches; do not combine V2 and V3 scores or mix judges in a single average. Judge calls can fail or return missing metrics; retain and report missing values.

To summarize one saved answer run and one judge without mixing experiments, use `v3\summarize_ragas.py PATH_TO_RUN --judge JUDGE_MODEL`. It reports coverage, missing IDs and means of available scores; incomplete means are not a full benchmark. It writes a separate timestamped summary.

## Separate Qwen experiment

`evaluate_qwen_v1.py` and `score_qwen_v1.py` use `qwen/qwen3.8-27b` for generation and judging without changing `.env` or the app. The Qwen agent uses separate schemas for scaling and conversion because the original combined schema returned missing arguments. The corresponding notebooks 11–13 document these new files. The 20-question generation run and the subsequent six-case calculator retest are saved separately in `results`; inspect both. Ragas scores are saved in `ragas_batch_qwen_*` and must not be mixed with scores from a different judge or generation run. A single model acting as both generator and judge may bias the results. These runs consume Groq quota.

## Remaining limitations

Reference answers and substitutions have been checked against the synthetic source but not independently reviewed or tested by a cook. Exact cooking times, allergen labels, personal dietary needs and suitability of substitutions remain unverified. Retrieval labels come from the same authored dataset and most questions name the target recipe. Ragas is an LLM judge and cannot establish real-world truth. The previous V2 benchmark uses a different corpus, older answers and partially missing judge scores; it is not a V3 benchmark.
