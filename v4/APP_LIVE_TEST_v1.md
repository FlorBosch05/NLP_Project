# V4 corrected app: live Qwen test

On 26 November 2026, `app_scale_v3.py` was exercised through Streamlit's test interface with the real Groq model `qwen/qwen3.8-27b` and the V4 recipe index. Eight turns completed without interface errors and with the expected route. The saved test checks routes and interface errors automatically; the answers and tool results below were also inspected against the stored recipe references.

| Scenario | Observed result |
| --- | --- |
| Guacamole ingredients | All seven source ingredients and their quantities were returned. |
| Follow-up serving count | Correctly retained Guacamole and answered four servings. |
| Follow-up scaling to eight | Correctly retained Guacamole, doubled linear amounts, flagged manual adjustments and warned that source instructions were unscaled. |
| Spanish tortilla method | Returned the source's principal preparation steps and times. |
| Ratatouille dietary tag | Reported the source's vegan tag and clarified it was not independently verified. |
| 2 kg to grams | MCP conversion returned 2,000 g. |
| Scale without a target | Asked how many servings were wanted. |
| Ratatouille from four to eight | MCP result and display included 1,200 g tomatoes, manual seasoning adjustments and the unscaled-instructions warning. |

The provider reported 9,647 input and 892 output tokens across the 17 recorded model calls. This is not a statement of remaining quota or billing. A preceding network-restricted attempt failed to connect and is saved separately; it did not demonstrate model behaviour.

This small sample is not a comprehensive benchmark, does not replace the prior retrieval Ragas evaluation, and does not independently verify publisher data or dietary safety. Manual scaling ingredients, original instructions and cooking times still require judgment.

Evidence: `results/app_live_qwen_v1_20261126_105957_946200.json`. Reproduce using `test_app_live_v1.py`; the corresponding notebook is `24_app_live_qwen_v1.ipynb`. The test uses the existing API key and consumes Groq quota.
