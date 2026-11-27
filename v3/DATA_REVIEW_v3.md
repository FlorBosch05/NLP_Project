# Version 3 corpus and reference review

## What was checked

All 30 V2 entries were read and revised for internal consistency. Each V3 recipe retains a name, ingredient list with units and positive quantities, instructions, an illustrative time estimate, servings, an ingredient-based dietary tag and provenance. An automated audit checks those fields, 13 retrieval references against selected corpus facts, four numeric conversion references and two scaling references. The greeting is not a single exact-answer case. See `results/data_audit_v3.json`; the code is in `audit_data.py`.

This is an AI-assisted consistency review, not an independent human audit. It cannot prove that an entire instruction is sound, that a dish tastes good, that a substitution works, that time estimates are accurate, or that an ingredient is safe for a person. The recipes were not cooked or verified against external recipe authors.

## Corrections made

- Clarified that the beans and chickpeas in five recipes are canned or fully cooked, avoiding an assumption that drained dry pulses are ready to eat. Dry lentil dishes now call for rinsing and package-specific cooking guidance. The [Food Standards Agency guidance on pulses](https://www.food.gov.uk/sites/default/files/media/document/sfbb-caterer-cooking-02-foods-that-need-extra-care_0.pdf) explains why dry pulses need appropriate preparation and notes that canned pulses are already cooked.
- Added the listed water or oil to steps where the V2 description omitted them, and made several preparation steps explicit without adding fabricated ingredient quantities.
- Replaced vague poultry, fish and egg-dish cooking instructions with temperature checks. These specific temperatures are drawn from the [FoodSafety.gov safe minimum temperature chart](https://www.foodsafety.gov/food-safety-charts/safe-minimum-internal-temperatures): poultry 74°C, fish 63°C and egg dishes 71°C. These are U.S. guidance; local advice can differ. A thermometer and safe handling still matter.
- Added an explicit substitution field to every recipe. Three recipes include clearly labelled, untested suggestions; all other recipes state that none is specified. Changed Q11–Q13 references to reflect the new version. Suggestions are not validated for allergens or personal diets.
- Kept dietary tags explicitly limited to listed ingredients and added a reminder that packaging, variants and cross-contact must be checked. No claim of allergen safety follows from a tag.
- Kept all 30 time estimates rather than fabricating evidence for them, and marked them as unverified. Some cooking methods still lack specific temperatures or independently measured durations.

## Remaining review required

A human should review each recipe and ingredient form, test recipes and cooking times, examine the three substitutions, and validate the 20 reference answers. The collection is intentionally minimal: for example, “chickpea curry” has no listed curry seasoning, and some sautéing instructions do not specify a cooking fat. These are unresolved culinary-quality issues, not verified finished dishes. Seek authoritative, local food-safety and allergy guidance before using these recipes in practice. In particular, a relevant ingredient list cannot prove safety from an allergen: labels and cross-contact matter. For cooked rice, storage is also important; see the [UK Food Standards Agency advice on reheating rice](https://www.food.gov.uk/safety-hygiene/home-food-fact-checker).

The source of each recipe remains “AI-created teaching recipe”; the external safety chart supports the temperature statements only, not the recipes, timings or dietary labels as a whole.
