# MVP options: comparison notebooks (version 1)

These notebooks supplement the existing v2 MVP. They do not change the app, the corpus or the existing notebooks. Start JupyterLab from this directory with the existing NLPproject virtual environment selected as its kernel. Install the optional packages in `requirements-comparisons.txt` into that environment if needed.

From this directory on Windows, start the supplied environment with `..\..\.venv\Scripts\python.exe -m jupyterlab`. To install optional packages, run `..\..\.venv\Scripts\python.exe -m pip install -r requirements-comparisons.txt`.

Read `08_mvp_option_map_v1.ipynb` first. The following notebooks provide executable experiments for chunking, vector stores and the two MCP patterns. The last notebook compares telemetry, evaluation and interface choices without presenting unmeasured results as facts. The experiments use the existing synthetic recipe data, local embeddings and a demonstration pantry. They do not consume Groq tokens, write to the MVP's vector store, or alter the user's pantry.

The retrieval measurements in the notebooks are small local demonstrations, not substitutes for the project’s incomplete Ragas benchmark. Run comparisons repeatedly with the same corpus, ground-truth queries, parameters and environment before drawing conclusions. The extra-credit section of the brief is not part of the MVP option comparison.

`results/comparison_snapshot_20261125_132206.json` records one actual run of the chunking and vector-store experiments. All approaches returned the target recipe within five hits for all ten named-recipe questions. This is a weak measure because the queries contain recipe names; it does not establish that the correct section was retrieved, or that these methods are equally effective on more realistic questions. Timings are single-run, in-memory measurements and should not be generalized.
