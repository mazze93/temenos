# Evaluations

Temenos keeps evaluation evidence separate from runtime code.

Four methods are recognized:

| Method | Use |
|---|---|
| deterministic | schema, invariants, serialization, policy mapping |
| behavioral | adversarial fixtures and regression cases |
| model_based | bounded evaluator experiments; never sole authority |
| human_review | claims requiring judgment or context |

A single aggregate score is intentionally avoided. A passing structural test
does not imply semantic correctness, and a model-based evaluator does not grant
authority to the artifact it grades.

Core dimensions are defined in `evaluations/rubrics/core.yaml`.
