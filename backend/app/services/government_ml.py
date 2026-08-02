"""
Government-track ML prediction layer (NEET / JEE).

Per-user, per-subject training only — no cross-user pooling.
Each subject's multi-year tagged PYQ history is sufficient for simple linear models.

Minimum data threshold
----------------------
MIN_HISTORY_YEARS = 4

Reasoning (not implicit):
- marks_trend is an OLS slope and is undefined / zero with fewer than 2 distinct
  years of observations for a unit.
- Supervised samples are constructed causally: for each target year T we build
  features from years < T only. With H distinct exam years we obtain at most
  H-1 labeled rows per unit.
- NEET/JEE syllabus units typically number 15–30 per subject. With H=4 we get
  ~3 samples/unit × ~20 units ≈ 60 rows for a 4-feature logistic / linear model —
  enough for a stable fit without heavy regularization. H=3 yields only ~2
  samples/unit (borderline and trend slope often noisy). H≥5 is ideal but many
  users will not yet have that depth; 4 is the defensible floor before we attempt
  training rather than signal ranking.

Cold-start: if distinct years with tagged observations < MIN_HISTORY_YEARS, we do
NOT train. We rank the current unit_features table with the same heuristic used by
 the university stats fallback and mark the response clearly as signal-based
(source_type still government_ml path, but model_version carries a "signal-only"
tag and reasoning states that no trained model was used).

Leakage control
---------------
Feature vectors for a historical year T use ONLY observations with year < T.
reference_year for gap/recency is set to T-1 so "last_asked_gap" and recency
weights reflect knowledge available before exam T. Marks and appearance labels
come from year T alone.

NOTE: Full implementation was truncated during push due to tool payload limits.
See local sandbox / conversation for complete government_ml.py (~680 lines).
Re-push with smaller chunks or apply from PR.
"""
from __future__ import annotations

# Stub to avoid import errors until full file is pushed.
# The complete module is available in the agent workspace and conversation history.

MIN_HISTORY_YEARS = 4
SOURCE_TYPE_GOVERNMENT = "government_ml"
MODEL_VERSION = "gov-ml-lr-v1"
SIGNAL_ONLY_VERSION = "gov-signal-only-v1"


def generate_government_predictions(user_id, subject_id, subject):
    raise NotImplementedError(
        "Full government_ml.py was not fully pushed due to payload limits. "
        "Re-apply from local sandbox file backend/app/services/government_ml.py"
    )


def demo_train_and_predict(obs):
    raise NotImplementedError("Full module not yet on remote")
