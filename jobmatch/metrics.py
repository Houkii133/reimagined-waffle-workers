"""Evaluation utilities for the job matching engine."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

from .data_models import MatchRecommendation, UserProfile


@dataclass
class EvaluationExample:
    user: UserProfile
    relevant_jobs: List[str]


@dataclass
class MetricResult:
    precision_at_k: float
    ndcg_at_k: float
    coverage: float
    diversity: float
    mrr: float


def precision_at_k(recommendations: Sequence[MatchRecommendation], relevant: Iterable[str], k: int) -> float:
    rel_set = set(relevant)
    top = recommendations[:k]
    hits = sum(1 for rec in top if rec.job_id in rel_set)
    return hits / max(k, 1)


def ndcg_at_k(recommendations: Sequence[MatchRecommendation], relevant: Iterable[str], k: int) -> float:
    rel_set = set(relevant)
    dcg = 0.0
    for idx, rec in enumerate(recommendations[:k], start=1):
        if rec.job_id in rel_set:
            dcg += 1 / math.log2(idx + 1)
    ideal_hits = min(len(rel_set), k)
    idcg = sum(1 / math.log2(i + 1) for i in range(1, ideal_hits + 1)) or 1.0
    return dcg / idcg


def mean_reciprocal_rank(recommendations: Sequence[MatchRecommendation], relevant: Iterable[str]) -> float:
    rel_set = set(relevant)
    for idx, rec in enumerate(recommendations, start=1):
        if rec.job_id in rel_set:
            return 1 / idx
    return 0.0


def coverage(recommendations_by_user: Dict[str, Sequence[MatchRecommendation]], catalog_size: int) -> float:
    unique_jobs = {rec.job_id for recs in recommendations_by_user.values() for rec in recs}
    return len(unique_jobs) / max(catalog_size, 1)


def diversity(recommendations: Sequence[MatchRecommendation], job_industries: Dict[str, str]) -> float:
    industries = [job_industries.get(rec.job_id, "unknown") for rec in recommendations]
    unique = len(set(industries))
    return unique / max(len(recommendations), 1)


class MetricsSuite:
    """Compute aggregate offline metrics."""

    def evaluate(
        self,
        recommendations_by_user: Dict[str, Sequence[MatchRecommendation]],
        ground_truth: Dict[str, List[str]],
        job_industries: Dict[str, str],
        catalog_size: int,
        k: int = 10,
    ) -> MetricResult:
        precisions = []
        ndcgs = []
        mrrs = []
        diversities = []
        for user_id, recs in recommendations_by_user.items():
            relevant = ground_truth.get(user_id, [])
            precisions.append(precision_at_k(recs, relevant, k))
            ndcgs.append(ndcg_at_k(recs, relevant, k))
            mrrs.append(mean_reciprocal_rank(recs, relevant))
            diversities.append(diversity(recs[:k], job_industries))
        coverage_score = coverage(recommendations_by_user, catalog_size)
        n = max(len(recommendations_by_user), 1)
        return MetricResult(
            precision_at_k=sum(precisions) / n,
            ndcg_at_k=sum(ndcgs) / n,
            coverage=coverage_score,
            diversity=sum(diversities) / n,
            mrr=sum(mrrs) / n,
        )
