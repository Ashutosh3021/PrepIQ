# Fix Phase C — Prediction + mock-test contracts

## Contracts

### Predictions
| Case | Behavior |
|------|----------|
| 0 papers / 0 questions | `source=no_data`, empty list, message, **no** DB row |
| 1–2 papers | `source=cold_start`, warning, LLM or stats |
| ≥3 papers | `source=full` (or `stats` if LLM down) |
| LLM missing/fail | stats fallback from unit frequency, `fallback_used=true` |

Normalized item fields (also used by tests weighting):
`question_number`, `text`, `question_text`, `topic`, `unit`, `marks`, `probability`, `confidence_score`, `reasoning`, `source`, `id`

### Mock tests
| Case | Behavior |
|------|----------|
| Empty pool | `test_id=none`, `status=error`, `error=insufficient_data`, **not** persisted |
| Submit `none` | **400** |
| No `correct_answer` on items | `score_percentage` / results `percentage` = **null** |
| Double submit | **400** |
| Source `predictions` | weighted by `confidence_score`; backfill from question bank |

## Live path
- API uses `app.services.prediction_service` only (not Bytez / old `PrepIQService` ORM path).
- Legacy `prediction_engine.py` may still exist for old callers; do not wire routers to it.

## Files
- `app/services/prediction_service.py` — normalize + honest coverage
- `app/routers/tests.py` — reject invalid test_id; null-safe scores
