from datetime import datetime, timezone

from jobmatch.data_models import Feedback
from jobmatch.learning import FeedbackLearner


def test_feedback_updates_weights_and_propensity():
    learner = FeedbackLearner()
    feedback_positive = Feedback(
        user_id="user-1",
        job_id="job-1",
        signal_type="apply",
        value=None,
        timestamp=datetime.now(timezone.utc),
    )
    learner.record(feedback_positive)
    learner.update_propensity(feedback_positive, score=0.7)
    weights = learner.get_weights("user-1")
    assert weights["hard"] > 0
    feedback_negative = Feedback(
        user_id="user-1",
        job_id="job-2",
        signal_type="dismiss",
        value=None,
        timestamp=datetime.now(timezone.utc),
    )
    learner.record(feedback_negative)
    learner.update_propensity(feedback_negative, score=0.3)
    assert learner.interactions("user-1") == 2
