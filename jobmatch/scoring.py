"""Scoring utilities for the hybrid ranker."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, List, Optional, Tuple

from .data_models import JobPosting, MatchRecommendation, UserProfile
from .normalization import (
    CurrencyConverter,
    SalaryBand,
    distance_decay,
    match_location,
    normalize_salary_range,
)
from .nlp import cosine_similarity


@dataclass
class ScoreComponents:
    hard: float
    soft: float
    title: float
    seniority: float
    industry: float
    location: float
    salary: float
    growth: float
    culture: float
    recency: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "hard": self.hard,
            "soft": self.soft,
            "title": self.title,
            "seniority": self.seniority,
            "industry": self.industry,
            "location": self.location,
            "salary": self.salary,
            "growth": self.growth,
            "culture": self.culture,
            "recency": self.recency,
        }


DEFAULT_WEIGHTS: Dict[str, float] = {
    "hard": 0.22,
    "soft": 0.10,
    "title": 0.15,
    "seniority": 0.10,
    "industry": 0.06,
    "location": 0.10,
    "salary": 0.07,
    "growth": 0.10,
    "culture": 0.06,
    "recency": 0.04,
}


def calibrate_score(raw_score: float) -> float:
    """Monotonically maps score to [0,1] using logistic transform."""

    return 1 / (1 + math.exp(-5 * (raw_score - 0.5)))


def blend_weights(preference: Optional[Dict[str, float]]) -> Dict[str, float]:
    if not preference:
        return DEFAULT_WEIGHTS
    total = sum(preference.values()) or 1.0
    blended = {k: preference.get(k, DEFAULT_WEIGHTS[k]) for k in DEFAULT_WEIGHTS}
    # Normalize to sum to 1.
    total = sum(blended.values()) or 1.0
    return {k: v / total for k, v in blended.items()}


def hard_skill_overlap(user_skills: Iterable[str], job_skills: Iterable[str]) -> Tuple[float, List[str]]:
    user_weights = {skill: distance_decay(idx) for idx, skill in enumerate(user_skills)}
    user_set = set(user_skills)
    job_set = set(job_skills)
    overlap = user_set.intersection(job_set)
    if not job_set:
        return 0.5, []
    denom = sum(user_weights.get(skill, 0.2) for skill in job_set) or 1.0
    numerator = sum(user_weights.get(skill, 0.0) for skill in overlap)
    score = numerator / denom
    return min(1.0, score), sorted(overlap)


def soft_skill_alignment(user_soft: Iterable[str], job_soft: Iterable[str]) -> Tuple[float, List[str]]:
    user_set = set(user_soft)
    job_set = set(job_soft)
    if not job_set:
        return 0.5, []
    overlap = user_set.intersection(job_set)
    score = len(overlap) / len(job_set)
    return min(1.0, score), sorted(overlap)


def title_similarity(user_roles: Iterable[str], desired_roles: Iterable[str], job_title_embedding: List[float], user_embedding: List[float]) -> float:
    return cosine_similarity(job_title_embedding, user_embedding)


def seniority_fit(years_experience: float, job_seniority: str) -> float:
    mapping = {"junior": 2, "mid": 5, "senior": 8, "lead": 11}
    target = mapping.get(job_seniority, 5)
    diff = abs(years_experience - target)
    return max(0.0, 1 - diff / 10)


def industry_alignment(user_industries: Iterable[str], job_industry: Optional[str]) -> float:
    if not job_industry:
        return 0.5
    if job_industry in user_industries:
        return 1.0
    if any(job_industry.split()[0] in industry for industry in user_industries):
        return 0.7
    return 0.2


def salary_fit(user_band: SalaryBand, job_band: SalaryBand) -> float:
    if job_band.min is None and job_band.max is None:
        return 0.5
    user_min = user_band.min or 0
    user_max = user_band.max or user_min
    job_min = job_band.min or job_band.max or 0
    job_max = job_band.max or job_band.min or job_min
    if job_max < user_min:
        return 0.0
    if job_min > user_max * 1.2:
        return 0.0
    overlap_min = max(user_min, job_min)
    overlap_max = min(user_max, job_max)
    if overlap_max < overlap_min:
        return 0.3
    width = max(user_max - user_min, 1.0)
    return max(0.0, min(1.0, (overlap_max - overlap_min) / width))


def growth_alignment(career_goals: str, growth_opps: Iterable[str]) -> Tuple[float, List[str]]:
    matched = [opp for opp in growth_opps if opp.lower() in career_goals.lower()]
    if not growth_opps:
        return 0.4, []
    score = len(matched) / len(growth_opps)
    return max(0.0, min(1.0, score)), matched


def culture_alignment(user_soft: Iterable[str], company_culture: Iterable[str]) -> Tuple[float, List[str]]:
    if not company_culture:
        return 0.4, []
    overlap = set(user_soft).intersection(company_culture)
    score = len(overlap) / len(set(company_culture))
    return max(0.0, min(1.0, score)), sorted(overlap)


def recency_score(posted_at: Optional[date], current_date: Optional[date] = None) -> float:
    if posted_at is None:
        return 0.5
    today = current_date or date.today()
    days = (today - posted_at).days
    if days <= 0:
        return 1.0
    return max(0.0, min(1.0, math.exp(-days / 60)))


def apply_hard_filters(
    user: UserProfile,
    job: JobPosting,
    job_features: Dict[str, object],
    converter: CurrencyConverter,
) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    # Work authorization
    if job.location.visa and job.location.visa not in user.work_auth:
        reasons.append("Visa/work authorization requirement not satisfied")

    # Location modality
    location_score, location_reasons = match_location(user.location_pref, job.location)
    if location_score == 0.0:
        reasons.append("Location modality mismatch")

    # Salary bounds
    user_band = normalize_salary_range(user.salary_min, user.salary_max, user.currency, converter)
    job_band = normalize_salary_range(
        job.compensation.min if job.compensation else None,
        job.compensation.max if job.compensation else None,
        job.compensation.currency if job.compensation else None,
        converter,
    )
    if job_band.min is not None and user_band.min is not None and job_band.max is not None:
        if job_band.max + 1e-9 < user_band.min:
            reasons.append("Salary below expectation")

    # Must-have skills
    must_haves: List[str] = job_features.get("must_haves", [])
    user_skills = {skill.lower() for skill in user.hard_skills}
    job_skills = {skill.lower() for skill in job_features.get("hard_skills", [])}
    for clause in must_haves:
        lowered = clause.lower()
        referenced = {skill for skill in job_skills if skill in lowered}
        if referenced and referenced.isdisjoint(user_skills):
            reasons.append(f"Missing must-have: {next(iter(referenced)).title()}")
            break

    blocked = bool(reasons)
    return blocked, reasons


def compute_score_components(
    user_profile: UserProfile,
    job_posting: JobPosting,
    user_features: Dict[str, object],
    job_features: Dict[str, object],
    converter: CurrencyConverter,
) -> Tuple[ScoreComponents, Dict[str, List[str]]]:
    rationale_fragments: Dict[str, List[str]] = {}

    hard_score, hard_overlap = hard_skill_overlap(user_features["hard_skills"], job_features["hard_skills"])
    rationale_fragments["hard"] = [f"Matches {len(hard_overlap)} hard skills"] if hard_overlap else []
    if hard_overlap:
        rationale_fragments["hard"].append(", ".join(sorted(hard_overlap)[:5]))

    soft_score, soft_overlap = soft_skill_alignment(user_features["soft_skills"], job_features["soft_skills"])
    if soft_overlap:
        rationale_fragments["soft"] = [f"Soft skills alignment: {', '.join(soft_overlap)}"]
    else:
        rationale_fragments["soft"] = []

    title_score = title_similarity(
        user_profile.roles_history,
        user_profile.desired_roles,
        job_features["embedding"],
        user_features["embedding"],
    )

    seniority_score = seniority_fit(user_profile.years_experience, job_features["seniority"])

    industry_score = industry_alignment(
        user_profile.industries_history,
        job_posting.company.industry,
    )

    location_score, location_reasons = match_location(user_profile.location_pref, job_posting.location)
    rationale_fragments["location"] = location_reasons

    user_band = normalize_salary_range(user_profile.salary_min, user_profile.salary_max, user_profile.currency, converter)
    job_band = normalize_salary_range(
        job_posting.compensation.min if job_posting.compensation else None,
        job_posting.compensation.max if job_posting.compensation else None,
        job_posting.compensation.currency if job_posting.compensation else None,
        converter,
    )
    salary_score = salary_fit(user_band, job_band)

    growth_score, growth_reasons = growth_alignment(user_profile.career_goals, job_posting.growth_opps)
    rationale_fragments["growth"] = [f"Growth: {', '.join(growth_reasons)}"] if growth_reasons else []

    culture_score, culture_reasons = culture_alignment(user_features["soft_skills"], job_posting.company_culture)
    rationale_fragments["culture"] = [f"Culture match: {', '.join(culture_reasons)}"] if culture_reasons else []

    recency = recency_score(job_posting.posted_at)

    components = ScoreComponents(
        hard=hard_score,
        soft=soft_score,
        title=title_score,
        seniority=seniority_score,
        industry=industry_score,
        location=location_score,
        salary=salary_score,
        growth=growth_score,
        culture=culture_score,
        recency=recency,
    )
    return components, rationale_fragments


def find_gaps(user_features: Dict[str, object], job_features: Dict[str, object]) -> List[str]:
    job_skills = set(job_features["hard_skills"])
    user_skills = set(user_features["hard_skills"])
    missing = sorted(job_skills - user_skills)
    return [f"Upskill: {skill}" for skill in missing[:5]]


def build_rationale(rationale_fragments: Dict[str, List[str]], components: ScoreComponents) -> List[str]:
    entries = []
    for key, reasons in rationale_fragments.items():
        if components.to_dict()[key] > 0.6 and reasons:
            entries.extend(reasons)
    if not entries:
        entries.append("Overall fit driven by complementary strengths")
    return entries[:6]


def compute_confidence(components: ScoreComponents, interactions: int) -> float:
    base = sum(components.to_dict().values()) / len(components.to_dict())
    history_boost = min(0.3, math.log1p(interactions) / 10)
    return max(0.1, min(1.0, base * 0.7 + history_boost))


def score_job(
    user_profile: UserProfile,
    job_posting: JobPosting,
    user_features: Dict[str, object],
    job_features: Dict[str, object],
    converter: CurrencyConverter,
    weights: Dict[str, float],
    interactions: int = 0,
) -> Tuple[float, ScoreComponents, Dict[str, List[str]]]:
    components, rationale = compute_score_components(
        user_profile,
        job_posting,
        user_features,
        job_features,
        converter,
    )
    weighted_sum = sum(getattr(components, key) * weights[key] for key in weights)
    score = calibrate_score(weighted_sum)
    return score, components, rationale
