from datetime import date

from jobmatch.data_models import JobLocation
from jobmatch.normalization import CurrencyConverter, Ontology, OntologyNormalizer, normalize_salary_range


def test_skill_normalization(tmp_path):
    ontology = Ontology.from_config("jobmatch/config/skill_synonyms.yaml")
    normalizer = OntologyNormalizer(ontology)
    skills = ["js", "ReactJS", "Python"]
    assert normalizer.normalize_skills(skills) == ["JavaScript", "React", "Python"]


def test_soft_skill_normalization():
    ontology = Ontology.from_config("jobmatch/config/skill_synonyms.yaml")
    normalizer = OntologyNormalizer(ontology)
    soft = ["communication skills", "team player", "ownership"]
    assert normalizer.normalize_soft_skills(soft) == ["communication", "teamwork", "ownership"]


def test_location_normalization():
    ontology = Ontology.from_config("jobmatch/config/skill_synonyms.yaml")
    normalizer = OntologyNormalizer(ontology)
    job_location = JobLocation(city="amsterdam", country="netherlands", remote=True)
    normalized = normalizer.normalize_location(job_location)
    assert normalized.city == "Amsterdam"
    assert normalized.country == "Netherlands"


def test_salary_conversion():
    converter = CurrencyConverter(base_currency="USD", rates={("EUR", "USD"): 1.1})
    band = normalize_salary_range(50000, 70000, "EUR", converter)
    assert band.min == 55000.0
    assert band.max == 77000.0
