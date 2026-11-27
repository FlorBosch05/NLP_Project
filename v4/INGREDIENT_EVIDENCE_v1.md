# Structured ingredient evidence: Ragas before and after

## Problem and version
The previous Ragas evaluation revealed that ingredient answers for Ratatouille (Q01), Dal tadka (Q04) and Borscht (Q05) were formatted directly from the stored `recipes_v4.json` record, but the displayed vector-retrieval context did not include the corresponding ingredients section. This made the source trace incomplete and left Ragas unable to verify many displayed quantities from the supplied context.

The separate `app_ollama_conversation_v8.py` uses `chef.conversation_v7` and `chef.structured_evidence_v1`. When a deterministic source-based answer is returned, the wrapper preserves the original vector hits and appends the exact ingredient list from the same structured record used by the answer. Metadata identifies the appended item as `structured_lookup`, includes the local data file, source, dataset version and licence, and gives it no similarity score. The UI notes that the trace can contain both vector-search results and structured lookups. This is additional structured evidence; it is not represented as a newly retrieved or re-ranked vector hit. The original app and earlier notebooks remain available.

## Validation of the change
- A test compared the appended JSON with the stored ingredients for **36/36** recipes and checked that the mock vector result and provenance were preserved. The three previously affected cases also passed live Streamlit UI checks with the actual index and local Qwen model. `results/evidence_tests_v2_20261126_230557_684500.json`.
- The new 20-case diagnostic returned the expected route for **20/20** and the expected deterministic MCP result for **6/6** tool cases. This is not a full answer-quality assessment. `results/diagnostic_evidence_v1_20261126_230614_515800.json`.
- The 11-turn existing safety UI regression passed: `results/safety_evidence_v1_20261126_231032_049600.json`. It is a limited safety sample, not a guarantee.
- In this particular paired run, all 13 retrieval answers were exactly identical to the earlier answer run, and all original vector-context strings were preserved in the same order. Q01–Q05 received one appended structured record each; Q06–Q13 had unchanged context. The extra record was appended even when an ingredients vector chunk was already present, so it can duplicate content and increases context size. For Q01–Q05 the addition ranged from 656 to 1,114 characters; characters are not model tokens.
- The source-section audit found the labelled section in **10/13** old contexts and **13/13** new contexts. Three of those new hits are direct structured lookups. This is evidence-availability improvement, not a claim that vector-retrieval ranking improved.

## Ragas rerun
The same 13 retrieval cases, stored answer references, local judge `qwen2.5:7b`, top-k setting and metric setup were used. Both runs have 13/13 scores for each metric; conversion, scaling and greeting cases are excluded from Ragas retrieval metrics. The same local model is used for generation and judging. The judge has an 8,192-token context and a 1,024-token output cap; source-derived references have not been independently reviewed.

| Metric | Before | After |
| --- | ---: | ---: |
| Context precision with reference | 0.832 | 0.838 |
| Context recall | 0.910 | 0.923 |
| Faithfulness | 0.706 | 0.877 |

Q01, Q04 and Q05 faithfulness changed from **0.000, 0.000, 0.083** to **1.000, 1.000, 1.000** respectively. This is consistent with supplying the missing structured evidence to the judge. It does not independently prove that the publisher's recipes are correct or that every possible answer is grounded. Q04 precision fell from 0.500 to 0.417 even though the added record is relevant; the record is appended after the vector hits, which can affect rank-sensitive scoring. Q02 and Q03 already contained an ingredient vector chunk before the fix; the new direct record is an additional trace of what the formatter actually used.

Unchanged Q07 and Q09 answers and contexts received different faithfulness scores across runs (1.000→0.800 and 1.000→0.500), illustrating judge variation. The source data and evaluation references are project-derived and not independently reviewed. These small-sample scores and an LLM judge do not establish a statistically robust improvement.

| Case | Context precision before → after | Context recall before → after | Faithfulness before → after |
| --- | ---: | ---: | ---: |
| Q01 | 0.500 → 0.500 | 1.000 → 1.000 | 0.000 → 1.000 |
| Q02 | 1.000 → 1.000 | 1.000 → 1.000 | 1.000 → 1.000 |
| Q03 | 0.478 → 0.525 | 1.000 → 1.000 | 1.000 → 1.000 |
| Q04 | 0.500 → 0.417 | 0.909 → 1.000 | 0.000 → 1.000 |
| Q05 | 0.583 → 0.646 | 0.917 → 1.000 | 0.083 → 1.000 |
| Q06 | 0.806 → 0.806 | 0.500 → 0.500 | 1.000 → 1.000 |
| Q07 | 1.000 → 1.000 | 1.000 → 1.000 | 1.000 → 0.800 |
| Q08 | 1.000 → 1.000 | 0.500 → 0.500 | 1.000 → 1.000 |
| Q09 | 1.000 → 1.000 | 1.000 → 1.000 | 1.000 → 0.500 |
| Q10 | 1.000 → 1.000 | 1.000 → 1.000 | 0.667 → 0.667 |
| Q11 | 1.000 → 1.000 | 1.000 → 1.000 | 1.000 → 1.000 |
| Q12 | 1.000 → 1.000 | 1.000 → 1.000 | 0.429 → 0.429 |
| Q13 | 0.950 → 1.000 | 1.000 → 1.000 | 1.000 → 1.000 |

## Remaining limitations
The Spanish tortilla case Q12 remains **0.429** for faithfulness: the answer contains the separately sourced 71°C egg-safety adaptation, which is not present in the recipe context provided to Ragas. The new change only addresses ingredient records; it does not resolve that different source-evidence mismatch. The Miso soup timing inconsistency and possible safety-classifier errors remain. A better evaluation would independently review references, provide appropriate safety-source evidence, use a separate judge, include held-out and multi-turn cases, and measure context-token cost.

## Saved evidence and reproduction
- Earlier answers: `results/diagnostic_conversation_v3_20261126_225338_066400.json`; earlier summary: `results/ragas_conversation_summary_v1_20261126_230037_317400.json`.
- New answers: `results/diagnostic_evidence_v1_20261126_230614_515800.json`; raw Ragas: `results/ragas_ollama_diagnostic_v2_20261126_230715_211300.json`; summary: `results/ragas_conversation_summary_v1_20261126_231008_352100.json`.
- Context audits: `results/ragas_context_audit_v1_20261126_225910_809000.json` and `results/ragas_context_audit_v1_20261126_230704_251000.json`.
- [Added ingredient record](results/screenshots_evidence_v1/01_ingredient_record.jpg) and [structured lookup provenance](results/screenshots_evidence_v1/02_lookup_provenance.jpg) are actual UI screenshots. The screenshot was captured before a sidebar explanation was added; the trace itself is unchanged.

From `NLPproject`, start Ollama and run `.\.venv\Scripts\python.exe -m streamlit run v4\app_ollama_conversation_v8.py`. To repeat Ragas, use the saved diagnostic and `ragas_ollama_diagnostic_v2.py`; it creates a new result file. The cells below reproduce versioned implementation and test files when run from `v4`; `%%writefile` overwrites files with the same name.
