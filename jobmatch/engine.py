"""JobMatchEngine orchestrates normalization, scoring, and learning."""

from __future__ import annotations

import json
import random
from dataclasses import replace
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .data_models import (
    DebugTrace,
    Feedback,
    JobPosting,
    MatchRecommendation,
    Telemetry,
    UserProfile,
    WhyNotExplanation,
)
from .datasets import DatasetFactory
from .learning import FeedbackLearner
from .metrics import MetricsSuite
from .nlp import FeatureExtractor, HashingEmbeddingProvider
from .normalization import CurrencyConverter, Ontology, OntologyNormalizer
from .scoring import (
    build_rationale,
    compute_confidence,
    find_gaps,
    score_job,
    apply_hard_filters,
    blend_weights,
)


class JobMatchEngine:
    """Hybrid intelligence engine for job recommendations."""

    def __init__(
        self,
        embedding_provider: Optional[HashingEmbeddingProvider] = None,
        skill_ontology: Optional[Ontology] = None,
        currency_converter: Optional[CurrencyConverter] = None,
        config_dir: Optional[str] = None,
        seed: int = 42,
        exploration_temperature: float = 0.05,
    ) -> None:
        base_path = Path(config_dir or Path(__file__).resolve().parent / "config")
        if skill_ontology is None:
            ontology_path = base_path / "skill_synonyms.yaml"
            skill_ontology = Ontology.from_config(str(ontology_path))
        self.ontology = skill_ontology
        self.normalizer = OntologyNormalizer(self.ontology)
        self.converter = currency_converter or CurrencyConverter()
        self.embedder = embedding_provider or HashingEmbeddingProvider()
        self.feature_extractor = FeatureExtractor(self.normalizer, self.embedder)
        self.telemetry = Telemetry()
        self.metrics = MetricsSuite()
        self.feedback = FeedbackLearner()
        self.seed = seed
        self.random = random.Random(seed)
        self.exploration_temperature = exploration_temperature
        self.jobs: Dict[str, JobPosting] = {}
        self.job_features: Dict[str, Dict[str, object]] = {}
        self.job_industries: Dict[str, str] = {}
        self._filter_reasons: Dict[Tuple[str, str], List[str]] = {}
        self._score_traces: Dict[Tuple[str, str], DebugTrace] = {}

    # ------------------------------------------------------------------
    # Ingestion & normalization
    # ------------------------------------------------------------------
    def ingest_jobs(self, jobs: Iterable[JobPosting]) -> None:
        """Normalize and index job postings."""

        for job in jobs:
            normalized_job = self._normalize_job(job)
            self.jobs[normalized_job.job_id] = normalized_job
            self.job_features[normalized_job.job_id] = self.feature_extractor.process_job(normalized_job)
            self.job_industries[normalized_job.job_id] = normalized_job.company.industry or "unknown"

    def _normalize_job(self, job: JobPosting) -> JobPosting:
        company = replace(
            job.company,
            industry=self.normalizer.normalize_industry(job.company.industry),
        )
        location = self.normalizer.normalize_location(job.location)
        normalized_job = replace(
            job,
            company=company,
            location=location,
            skills=self.normalizer.normalize_skills(job.skills),
            responsibilities=[resp.strip() for resp in job.responsibilities],
            requirements=[req.strip() for req in job.requirements],
            growth_opps=[opp.lower() for opp in job.growth_opps],
            company_culture=[culture.lower() for culture in job.company_culture],
            seniority=self.normalizer.normalize_seniority(job.seniority),
        )
        return normalized_job

    def _normalize_user(self, user: UserProfile) -> UserProfile:
        return replace(
            user,
            hard_skills=self.normalizer.normalize_skills(user.hard_skills),
            soft_skills=self.normalizer.normalize_soft_skills(user.soft_skills),
            roles_history=self.normalizer.normalize_roles(user.roles_history),
            desired_roles=self.normalizer.normalize_roles(user.desired_roles),
            industries_history=[self.normalizer.normalize_industry(ind) or ind for ind in user.industries_history],
            desired_industries=[self.normalizer.normalize_industry(ind) or ind for ind in user.desired_industries],
            location_pref=self.normalizer.normalize_location_pref(user.location_pref),
        )

    # ------------------------------------------------------------------
    # Recommendation loop
    # ------------------------------------------------------------------
    def recommend(self, user_profile: UserProfile, top_k: int = 20) -> List[MatchRecommendation]:
        """Return ranked job recommendations."""

        user = self._normalize_user(user_profile)
        user_features = self.feature_extractor.process_user(user)
        learned_weights = self.feedback.get_weights(user.user_id)
        pref_weights = blend_weights(user.preference_weights)
        weights = {
            key: (learned_weights[key] + pref_weights[key]) / 2 for key in pref_weights
        }
        user_interactions = self.feedback.interactions(user.user_id)
        recommendations: List[Tuple[float, MatchRecommendation]] = []
        rng = random.Random(self.seed + hash(user.user_id))

        for job_id, job in self.jobs.items():
            job_features = self.job_features[job_id]
            blocked, reasons = apply_hard_filters(user, job, job_features, self.converter)
            key = (user.user_id, job_id)
            if blocked:
                self._filter_reasons[key] = reasons
                for reason in reasons:
                    self.telemetry.increment(reason)
                continue
            score, components, rationale_fragments = score_job(
                user,
                job,
                user_features,
                job_features,
                self.converter,
                weights,
                interactions=user_interactions,
            )
            propensity = self.feedback.propensity(score)
            exploration = rng.random() * self.exploration_temperature
            final_score = max(0.0, min(1.0, score * 0.8 + propensity * 0.2 + exploration))
            rationale = build_rationale(rationale_fragments, components)
            gaps = find_gaps(user_features, job_features)
            confidence = compute_confidence(components, user_interactions)
            recommendation = MatchRecommendation(
                job_id=job_id,
                score=final_score,
                rank=0,
                rationale=rationale,
                qualification_gaps=gaps,
                fit_dimensions=components.to_dict(),
                confidence=confidence,
            )
            recommendations.append((final_score, recommendation))
            self._score_traces[key] = DebugTrace(
                seed=self.seed,
                features={**components.to_dict()},
                scores={"raw": score, "final": final_score, "propensity": propensity},
                weights=weights,
                rationale=rationale,
            )

        ranked = [rec for _, rec in sorted(recommendations, key=lambda item: item[0], reverse=True)][:top_k]
        for idx, rec in enumerate(ranked, start=1):
            rec.rank = idx
        return ranked

    # ------------------------------------------------------------------
    # Feedback and learning
    # ------------------------------------------------------------------
    def record_feedback(self, feedback: Feedback) -> None:
        key = (feedback.user_id, feedback.job_id)
        trace = self._score_traces.get(key)
        score = trace.scores["final"] if trace else 0.5
        self.feedback.record(feedback)
        self.feedback.update_propensity(feedback, score)

    # ------------------------------------------------------------------
    # Explainability utilities
    # ------------------------------------------------------------------
    def why_not(self, user_profile: UserProfile, job_id: str) -> WhyNotExplanation:
        user = self._normalize_user(user_profile)
        key = (user.user_id, job_id)
        if key not in self._filter_reasons:
            job = self.jobs.get(job_id)
            if not job:
                return WhyNotExplanation(job_id=job_id, blocked=True, reasons=["Job not found"])
            job_features = self.job_features[job_id]
            blocked, reasons = apply_hard_filters(user, job, job_features, self.converter)
            return WhyNotExplanation(job_id=job_id, blocked=blocked, reasons=reasons or ["No blockers"])
        return WhyNotExplanation(job_id=job_id, blocked=True, reasons=self._filter_reasons[key])

    def what_if(self, user_profile: UserProfile, changes: Dict[str, object], top_k: int = 10) -> List[MatchRecommendation]:
        user = self._normalize_user(user_profile)
        mutable = user
        if "add_skills" in changes:
            add_skills = self.normalizer.normalize_skills(changes["add_skills"])
            mutable = replace(mutable, hard_skills=sorted(set(mutable.hard_skills).union(add_skills)))
        if "relocate" in changes:
            pref = mutable.location_pref
            updated_pref = replace(pref, cities=list(set(pref.cities + [changes["relocate"].title()])))
            mutable = replace(mutable, location_pref=updated_pref)
        return self.recommend(mutable, top_k=top_k)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------
    def evaluate(
        self,
        user_profiles: Dict[str, UserProfile],
        ground_truth: Dict[str, List[str]],
        top_k: int = 10,
    ) -> Dict[str, float]:
        recs = {
            user_id: self.recommend(profile, top_k)
            for user_id, profile in user_profiles.items()
        }
        result = self.metrics.evaluate(recs, ground_truth, self.job_industries, len(self.jobs), k=top_k)
        return result.__dict__

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def trace(self, user_id: str, job_id: str) -> Optional[DebugTrace]:
        return self._score_traces.get((user_id, job_id))

    def load_synthetic(self, users: int = 20, jobs: int = 200) -> Tuple[List[UserProfile], List[JobPosting]]:
        dataset = DatasetFactory(seed=self.seed).build(users=users, jobs=jobs)
        self.ingest_jobs(dataset.jobs)
        return dataset.users, dataset.jobs

    def telemetry_snapshot(self) -> Dict[str, Dict[str, int]]:
        return {"filtered": dict(self.telemetry.filtered_counts)}

    def dump_state(self) -> Dict[str, object]:
        return {
            "jobs": list(self.jobs.keys()),
            "feedback": json.dumps(self.feedback.user_weights),
        }
