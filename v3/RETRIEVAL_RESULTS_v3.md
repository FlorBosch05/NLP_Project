# Version 3 retrieval comparison

`results/retrieval_comparison_20261125_132837.json` records an offline test of section chunks versus complete-recipe chunks using the same V3 corpus, embedding model, 13 retrieval queries and top-k of 5.

| Measure | Sections | Whole recipe |
|---|---:|---:|
| Expected recipe in top 5 | 13/13 | 13/13 |
| Labelled evidence section in top 5, or whole parent | 13/13 | 13/13 |
| Mean retrieved context size, embedding-tokenizer estimate | 245 | 917.4 |

For this small test, sections returned the labelled evidence with about 73% fewer estimated context tokens. This supports retaining sections as a **provisional** default. The token count is a proxy from the embedding tokenizer, not the Groq model’s billable token count. The questions usually contain the recipe name, the reference labels were AI-authored from the same synthetic data, and an exact section label does not establish that a generated answer is correct. The test is not Ragas and it does not establish general superiority. Measure Ragas precision, recall and faithfulness, actual prompt tokens and answer quality for both strategies on independently reviewed questions before drawing a stronger conclusion.

In these 13 cases the labelled section or recipe also ranked first every time. Because each case has only one labelled target among five results, its exact-label precision@5 is 0.2 under this narrow definition; other chunks may contain useful context that the label does not credit. A smaller top-k is worth testing for cost, but these easy, named-recipe queries do not test multi-section questions. The current default stays at 5 until broader cases and answer-quality evaluation justify a change.

The data differs from V2: Q11–Q13 now test actual, unverified substitution suggestions. V2's saved generated answers and Ragas scores must not be mixed with V3 scores. A Ragas judge using a different model must be labelled and analysed separately as well.
