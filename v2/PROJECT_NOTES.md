# Project notes and oral defense

## Problem and scope

Flavor Chef answers questions about a small recipe collection, scales ingredients, and converts compatible kitchen units. It uses Groq for language-model calls; the retrieval index and interface run locally. The corpus is synthetic and is intended for a teaching demonstration, not culinary or allergy advice.

## Design choices

- **Data:** 30 structured synthetic recipes with ingredient quantities, instructions, serving counts, estimated times and dietary tags. The tags are based on listed ingredients only. The data and reference answers still need independent human review.
- **Retrieval:** a local sentence-transformer creates embeddings and Chroma stores them. Sections retain the recipe name and section metadata. The alternative full-recipe chunking baseline is selectable in the UI and evaluation script. The content fingerprint makes the chosen index reusable and rebuilds it when the corpus or embedding model changes.
- **Agent state:** LangGraph carries the request, recent conversation, rewritten retrieval query, source fragments, tool result and model-call telemetry. The model chooses a path; the graph executes it. A follow-up question can use recent conversation for routing and query rewriting.
- **Tool boundary:** MCP exposes scaling and same-dimension unit conversion. For a known recipe, scaling takes original quantities and servings from the dataset, not model-generated quantities. The model extracts the target; MCP performs arithmetic and validates the arguments. Ambiguous recipe selection prompts for clarification. This design still requires testing because the model can misinterpret the desired serving count.
- **Evaluation:** 20 fixed cases cover retrieval, absent substitution evidence, conversion, scaling and chat. Three Ragas metrics score retrieved-context cases; all cases record routing, final answers and any tool calls. Top-k retrieval cannot prove that a substitution is absent from the whole corpus: these questions test whether the answer respects the evidence actually retrieved. The judge and the assistant use Groq and can make mistakes. Evaluate tool correctness directly as well as reading the answer.
- **Observability:** the UI shows retrieved sources, route, tool inputs and outputs, per-call token usage, timing, total time and final-answer time to first token. Counts can be unavailable if the provider omits them. Execution traces are displayed locally; LangSmith is optional and is not configured.

## Failure analysis guide

For a wrong answer, inspect the route first. If a needed recipe was not retrieved, check the standalone query, top-k and chunk strategy. If relevant evidence is present but the answer misstates it, inspect the prompt and faithfulness. For a wrong calculation, inspect the MCP arguments before the result: correct arithmetic cannot fix incorrect inputs. Check whether a failure is due to a provider or quota error before changing the model or retrieval system. Compare results only on the same dataset and configuration.

## AI use and accountability

The initial prototype and this version were generated and revised with Codex. Synthetic recipes and evaluation references were authored with AI assistance; they are not independently validated. Record further edits, test results, and any outside sources as the project evolves. Before the oral defense, personally inspect the code, validate representative recipes and reference answers, and be ready to explain and run each part without AI assistance. Do not represent this note as a substitute for the course's GenAI policy.
