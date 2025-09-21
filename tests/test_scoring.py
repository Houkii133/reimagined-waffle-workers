from datetime import date

from jobmatch.data_models import (
    Availability,
    CompanyInfo,
    Compensation,
    EducationEntry,
    JobLocation,
    JobPosting,
    LocationPreference,
    UserProfile,
)
from jobmatch.nlp import FeatureExtractor, HashingEmbeddingProvider
from jobmatch.normalization import CurrencyConverter, Ontology, OntologyNormalizer
from jobmatch.scoring import (
    ScoreComponents,
    apply_hard_filters,
    blend_weights,
    find_gaps,
    score_job,
)


def build_user() -> UserProfile:
    ontology = Ontology.from_config("jobmatch/config/skill_synonyms.yaml")
    normalizer = OntologyNormalizer(ontology)
    pref = normalizer.normalize_location_pref(
        LocationPreference(cities=["Amsterdam"], countries=["Netherlands"], remote=True, hybrid=True, onsite=False)
    )
    user = UserProfile(
        user_id="user-1",
        hard_skills=["Python", "React", "SQL"],
        soft_skills=["communication", "ownership"],
        years_experience=6,
        roles_history=["Data Engineer"],
        industries_history=["FinTech"],
        education=[EducationEntry(level="Bachelors", field="CS", institution="Uni")],
        certifications=[],
        portfolio_links=[],
        desired_roles=["Data Engineer"],
        desired_industries=["FinTech"],
        salary_min=80000,
        salary_max=120000,
        currency="USD",
        location_pref=pref,
        work_auth=["EU"],
        availability=Availability(start_date=date.today(), notice_period_days=30),
        career_goals="Build reliable data systems",
        constraints=[],
        preference_weights=None,
    )
    return user


def build_job() -> JobPosting:
    return JobPosting(
        job_id="job-1",
        title="Data Engineer",
        company=CompanyInfo(name="FinBank", industry="FinTech"),
        description="Looking for a data engineer with Python and SQL",
        requirements=["Must have Python", "Required SQL"],
        responsibilities=["Build pipelines"],
        skills=["Python", "SQL", "Airflow"],
        seniority="mid",
        location=JobLocation(city="Amsterdam", country="Netherlands", remote=True, onsite=False, hybrid=True),
        compensation=Compensation(min=85000, max=115000, currency="USD", type="salary"),
        benefits=[],
        team_signals=["mentorship"],
        growth_opps=["manager_track"],
        company_culture=["ownership", "collaboration"],
        posted_at=date.today(),
    )


def test_hard_filters_pass():
    ontology = Ontology.from_config("jobmatch/config/skill_synonyms.yaml")
    normalizer = OntologyNormalizer(ontology)
    user = build_user()
    job = build_job()
    engine_normalizer = OntologyNormalizer(ontology)
    extractor = FeatureExtractor(engine_normalizer, HashingEmbeddingProvider())
    job_features = extractor.process_job(job)
    converter = CurrencyConverter()
    blocked, reasons = apply_hard_filters(user, job, job_features, converter)
    assert not blocked
    assert reasons == []


def test_score_job_components():
    ontology = Ontology.from_config("jobmatch/config/skill_synonyms.yaml")
    normalizer = OntologyNormalizer(ontology)
    user = build_user()
    job = build_job()
    extractor = FeatureExtractor(normalizer, HashingEmbeddingProvider())
    user_features = extractor.process_user(user)
    job_features = extractor.process_job(job)
    converter = CurrencyConverter()
    weights = blend_weights(None)
    score, components, rationale = score_job(user, job, user_features, job_features, converter, weights)
    assert 0 <= score <= 1
    assert isinstance(components, ScoreComponents)
    assert "hard" in components.to_dict()
    assert "hard" in rationale


def test_find_gaps_identifies_missing_skill():
    ontology = Ontology.from_config("jobmatch/config/skill_synonyms.yaml")
    normalizer = OntologyNormalizer(ontology)
    user = build_user()
    job = build_job()
    extractor = FeatureExtractor(normalizer, HashingEmbeddingProvider())
    user_features = extractor.process_user(user)
    job_features = extractor.process_job(job)
    gaps = find_gaps(user_features, job_features)
    assert any("Airflow" in gap for gap in gaps)
