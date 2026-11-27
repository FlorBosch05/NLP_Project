# V4 Qwen Ragas evaluation — completed

This report extends `QWEN_EVALUATION_v1.md` without replacing it. It scores the 13 retrieved-answer cases from `results/evaluation_qwen_v1_sections_k5_20261125_191925.json` using `qwen/qwen3.8-27b` as the Ragas judge. The generator and judge were the same model, so the scores may be biased. The 20 source-derived references and published recipe data have not been independently reviewed by this project.

All 13 cases now have all three scores. The mean context precision is **0.84498**, context recall **1.00000**, and faithfulness **0.93609**. These are LLM-judge metrics on a small dataset, not proof of real-world correctness or dietary safety.

The original Q01–Q06 scores and failed Q07 attempt are in `results/ragas_qwen_v1_20261125_192005_072400.json`. The resumed Q07–Q13 batch is in `results/ragas_qwen_v1_20261126_090021_291300.json`. Groq rejected the Q13 context-precision and faithfulness requests because their expected output exceeded the output-per-minute allowance. A separate retry, `results/ragas_qwen_v2_20261126_090903_191700.json`, uses the same inputs and judge with a 900-token maximum output per judge request and has all three Q13 scores. A response cap may affect generation; the setting is recorded explicitly.

`results/ragas_summary_qwen_v2_20261126_091012_093300.json` combines only the same answer run and judge, selecting the latest result for each case. It reports all 13 cases for every metric and no missing scores. It includes the capped Q13 retry; it does not combine models or corpora.

The generation run reported 26,179 tokens. Across all saved judge attempts for this answer run, including the failed Q07 and partial Q13 attempts and the successful retry, callbacks reported 144,913 judge tokens. The combined reported total is **171,092** tokens. This is provider-reported usage from recorded calls; it may omit failed or unreported calls and is not a bill or a statement of remaining quota.

Ragas covers only the retrieval answers. The earlier 20-question run chose the expected route for 20/20 cases, and all six MCP tool results matched. It also exposed unscaled source instructions in a scaled Ratatouille answer. The separate scaling-display fix passed an offline test but has not been live-tested with Qwen; the Ragas results do not validate it. The source's Miso soup description and structured time fields also conflict and need human review.
