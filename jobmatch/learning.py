"""Online personalization and feedback learning."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict

from .data_models import Feedback
from .scoring import DEFAULT_WEIGHTS


SIGNAL_IMPACTS: Dict[str, Dict[str, float]] = {
    "apply": {"hard": 0.02, "growth": 0.02, "culture": 0.01},
    "save": {"culture": 0.015, "growth": 0.01},
    "click": {"title": 0.01, "hard": 0.005},
    "dismiss": {"hard": -0.03, "culture": -0.02},
    "reject": {"salary": -0.03, "location": -0.02},
    "accept": {"salary": 0.03, "culture": 0.02},
    "rating": {"hard": 0.02, "soft": 0.02},
}

POSITIVE_SIGNALS = {"apply", "accept", "save"}
NEGATIVE_SIGNALS = {"dismiss", "reject"}


@dataclass
class FeedbackLearner:
    """Updates per-user preferences and a simple propensity model."""

    learning_rate: float = 0.1
    user_weights: Dict[str, Dict[str, float]] = field(default_factory=dict)
    interaction_counts: Dict[str, int] = field(default_factory=dict)
    propensity_alpha: float = 1.0
    propensity_bias: float = 0.0

    def record(self, feedback: Feedback) -> None:
        self.interaction_counts[feedback.user_id] = self.interaction_counts.get(feedback.user_id, 0) + 1
        impacts = SIGNAL_IMPACTS.get(feedback.signal_type, {})
        prefs = self.user_weights.setdefault(feedback.user_id, {k: 0.0 for k in DEFAULT_WEIGHTS})
        for key, delta in impacts.items():
            prefs[key] += delta

    def get_weights(self, user_id: str) -> Dict[str, float]:
        adjustments = self.user_weights.get(user_id, {})
        weights = {k: DEFAULT_WEIGHTS[k] + adjustments.get(k, 0.0) for k in DEFAULT_WEIGHTS}
        total = sum(weights.values()) or 1.0
        return {k: max(0.0, v) / total for k, v in weights.items()}

    def propensity(self, score: float) -> float:
        return 1 / (1 + math.exp(-(self.propensity_alpha * score + self.propensity_bias)))

    def update_propensity(self, feedback: Feedback, score: float) -> None:
        if feedback.signal_type not in POSITIVE_SIGNALS.union(NEGATIVE_SIGNALS):
            return
        target = 1.0 if feedback.signal_type in POSITIVE_SIGNALS else 0.0
        pred = self.propensity(score)
        error = target - pred
        self.propensity_alpha += self.learning_rate * error * score
        self.propensity_bias += self.learning_rate * error

    def interactions(self, user_id: str) -> int:
        return self.interaction_counts.get(user_id, 0)
