# V4 scaling: live Qwen verification

Date: 26 November 2026. Model: `qwen/qwen3.8-27b`.

The separately versioned `app_scale_v3.py` uses `chef/agent_scale_v3.py`. It preserves the deterministic results from the scaling tool and makes clear that the original preparation steps and cooking times have not been scaled. Ingredients marked for manual adjustment remain manual, and missing source quantities are not invented.

## Results

- The earlier scaling fix passed live Qwen checks for Ratatouille (4 to 8 servings) and Guacamole (4 to 2).
- Additional live checks covered Miso soup, Paella valenciana, Borscht, a Guacamole follow-up, and a question without a target serving count. Those checks revealed that the missing-count response exposed an internal instruction. Version 3 fixes this by asking the user directly: “How many servings would you like?”
- Version 3 passed live Qwen checks for Ratatouille and the missing-count case. Both were also tested through the Streamlit interface with Qwen; the scaled quantities and the missing-count question appeared without application errors.
- An independent offline regression invoked the actual local MCP scaling tool for all 36 V4 recipes at twice their original serving count. All 36 passed checks against their stored ingredient rules, including fixed, linear, manual and unspecified quantities.

The full-catalog check validates the tool at one scaling factor; live model routing was sampled, so these results do not guarantee every possible prompt or serving count. Ingredients marked for manual adjustment still need the cook's judgment. Original instructions and cooking times remain unscaled.

## Run the verified version

From the `NLPproject` directory in PowerShell, using the existing Groq API key configuration:

```powershell
$env:GROQ_MODEL = "qwen/qwen3.8-27b"
.\.venv\Scripts\python.exe -m streamlit run v4\app_scale_v3.py
```

The model setting above applies to the current PowerShell session. The original app and earlier versions remain available.

## Evidence and reproducibility

- `results/evaluation_qwen_scale_v2_sections_k5_20261126_095423.json`: two original live checks.
- `results/scaling_live_qwen_v1_20261126_095543_806400.json`: additional live checks of the earlier fix.
- `results/scaling_live_qwen_v2_20261126_095722_632400.json`: live checks of version 3.
- `results/scaling_all_recipes_v1_20261126_095912_154100.json`: all-recipe MCP regression.
- `19_scale_live_qwen_v1.ipynb`, `20_scale_agent_v3.ipynb`, `21_scale_app_v3.ipynb`, `22_scale_live_qwen_v2.ipynb`, and `23_all_recipe_scaling_v1.ipynb`: separate notebook versions of the test and implementation files.
