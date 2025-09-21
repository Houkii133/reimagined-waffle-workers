from datetime import datetime, timezone

from jobmatch.data_models import Feedback
from jobmatch.engine import JobMatchEngine
from jobmatch.nlp import HashingEmbeddingProvider


def test_engine_recommendations_workflow():
    engine = JobMatchEngine(embedding_provider=HashingEmbeddingProvider(dim=64), seed=7)
    users, jobs = engine.load_synthetic(users=5, jobs=30)
    user = users[0]
    recs = engine.recommend(user, top_k=5)
    assert len(recs) == 5
    assert recs[0].score >= recs[-1].score
    feedback = Feedback(
        user_id=user.user_id,
        job_id=recs[0].job_id,
        signal_type="apply",
        value=None,
        timestamp=datetime.now(timezone.utc),
    )
    engine.record_feedback(feedback)
    assert engine.feedback.interactions(user.user_id) == 1
    why_not = engine.why_not(user, "non-existent")
    assert why_not.blocked
    assert "Job not found" in why_not.reasons[0]
    exploration = engine.what_if(user, {"add_skills": ["Kubernetes"]}, top_k=3)
    assert len(exploration) == 3


def test_engine_telemetry_snapshot():
    engine = JobMatchEngine(seed=11)
    users, jobs = engine.load_synthetic(users=2, jobs=5)
    user = users[0]
    engine.recommend(user, top_k=3)
    snapshot = engine.telemetry_snapshot()
    assert "filtered" in snapshot
