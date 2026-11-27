# Evaluation notes

The first full 20-case run on the corrected scaling and conversion workflow routed all 20 cases as expected. The four conversion results and two scaling results matched their reference values. The recorded requests, source chunks, responses and tool calls are stored in the timestamped `results/evaluation_sections_k5_20261125_130014.json` file.

Manual inspection of Q03 found an answer expanded the short lentil-soup instructions with details that were not explicitly present in the source. After this run, the answer prompt was tightened to request only the asked-for information and avoid adding unsupported steps. A single repeat remained more detailed than the source, so the issue is not fully resolved. Rerun the same cases and compare faithfulness and individual answers. The routing and tool checks in the earlier result were performed before that prompt change.

A separate live follow-up test asked for tomato pasta and then asked to make it for four servings. The agent selected the scaling path and returned 400 g pasta, 600 g tomatoes and 30 ml olive oil. One successful follow-up does not establish general reliability.

An initial one-question Ragas smoke test returned context precision 0.33, context recall 1.0 and faithfulness 0.25. These are judge outputs for one synthetic case and cannot establish overall performance. Inspect the retrieved contexts, answer and judge behavior before interpreting them. The full evaluation may take a long time on the free tier, and judge scores can be missing when calls fail or hit quota limits.

The later saved-answer benchmark produced partial Ragas results for Q01–Q05 in the `ragas_batch` files. Q03 has no faithfulness score because the judge did not finish; Q05 has no recall score after a Groq rate-limit error. Q06–Q13 have not been scored. The full benchmark is therefore incomplete: use `score_saved.py` with the relevant offsets to retry missing cases and metrics. The 20-case routing/tool run is complete, but it is not a replacement for full Ragas scores.

The dataset and expected answers were AI-assisted and have not been independently reviewed. Neither the evaluation nor these synthetic examples establish food or allergy safety.
