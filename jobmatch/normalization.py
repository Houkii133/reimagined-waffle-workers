"""Normalization utilities and ontologies."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

from .data_models import JobLocation, LocationPreference


@dataclass
class CurrencyConverter:
    """Interface for currency conversion strategies."""

    base_currency: str = "USD"
    rates: Dict[Tuple[str, str], float] = field(default_factory=dict)

    def convert(self, amount: Optional[int], from_currency: Optional[str]) -> Optional[float]:
        """Convert ``amount`` to the base currency if exchange rate is known."""

        if amount is None or from_currency is None:
            return None
        if from_currency == self.base_currency:
            return round(float(amount), 2)
        key = (from_currency.upper(), self.base_currency.upper())
        rate = self.rates.get(key)
        if rate is None:
            # Fallback to identity when rate missing to keep deterministic behavior.
            return round(float(amount), 2)
        return round(float(amount) * rate, 2)


@dataclass
class Ontology:
    """Represents canonical vocabularies for normalization."""

    skills: Dict[str, str]
    soft_skills: Dict[str, str]
    roles: Dict[str, str]
    seniority: Dict[str, str]
    industries: Dict[str, str]

    @classmethod
    def from_config(cls, path: str) -> "Ontology":
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
        try:
            import yaml  # type: ignore

            payload = yaml.safe_load(raw)
        except ModuleNotFoundError:  # pragma: no cover - executed in minimal environments
            payload = cls._parse_simple_yaml(raw)
        return cls(
            skills={k.lower(): v for k, v in payload.get("skills", {}).items()},
            soft_skills={k.lower(): v for k, v in payload.get("soft_skills", {}).items()},
            roles={k.lower(): v for k, v in payload.get("roles", {}).items()},
            seniority={k.lower(): v for k, v in payload.get("seniority", {}).items()},
            industries={k.lower(): v for k, v in payload.get("industries", {}).items()},
        )

    @staticmethod
    def _parse_simple_yaml(raw: str) -> Dict[str, Dict[str, str]]:
        payload: Dict[str, Dict[str, str]] = {}
        current: Optional[str] = None
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.endswith(":"):
                current = line[:-1]
                payload[current] = {}
            elif ":" in line and current:
                key, value = line.split(":", 1)
                payload[current][key.strip()] = value.strip()
        return payload

    def canonical(self, value: str, domain: str) -> str:
        mapping = getattr(self, domain)
        return mapping.get(value.lower(), value)


@dataclass
class OntologyNormalizer:
    """Normalize free text strings into canonical ontology entries."""

    ontology: Ontology

    def normalize_skills(self, skills: Iterable[str]) -> List[str]:
        seen: List[str] = []
        for skill in skills:
            if not skill:
                continue
            canonical = self.ontology.canonical(skill.strip(), "skills")
            if canonical not in seen:
                seen.append(canonical)
        return seen

    def normalize_soft_skills(self, skills: Iterable[str]) -> List[str]:
        seen: List[str] = []
        for skill in skills:
            if not skill:
                continue
            canonical = self.ontology.canonical(skill.strip(), "soft_skills")
            if canonical not in seen:
                seen.append(canonical)
        return seen

    def normalize_roles(self, roles: Iterable[str]) -> List[str]:
        seen: List[str] = []
        for role in roles:
            if not role:
                continue
            canonical = self.ontology.canonical(role.strip(), "roles")
            if canonical not in seen:
                seen.append(canonical)
        return seen

    def normalize_seniority(self, seniority: str) -> str:
        return self.ontology.canonical(seniority, "seniority")

    def normalize_industry(self, industry: Optional[str]) -> Optional[str]:
        if not industry:
            return None
        return self.ontology.canonical(industry, "industries")

    def normalize_location(self, location: JobLocation) -> JobLocation:
        city = location.city.title() if location.city else None
        country = location.country.title() if location.country else None
        return JobLocation(
            city=city,
            country=country,
            remote=location.remote,
            hybrid=location.hybrid,
            onsite=location.onsite,
            visa=location.visa,
        )

    def normalize_location_pref(self, pref: LocationPreference) -> LocationPreference:
        return LocationPreference(
            cities=[c.title() for c in pref.cities],
            countries=[c.title() for c in pref.countries],
            remote=pref.remote,
            hybrid=pref.hybrid,
            onsite=pref.onsite,
            relocation=pref.relocation,
        )


def scrub_pii(text: str) -> str:
    """Basic PII scrubber removing email addresses and phone numbers."""

    text = re.sub(r"[\w.]+@[\w.]+", "<email>", text)
    text = re.sub(r"\+?\d[\d\-\s]{6,}\d", "<phone>", text)
    return text


def distance_decay(index: int, decay: float = 0.8) -> float:
    """Compute exponential decay for recency weighting."""

    return math.pow(decay, index)


@dataclass
class SalaryBand:
    """Normalized salary band in canonical currency."""

    min: Optional[float]
    max: Optional[float]


def normalize_salary_range(
    minimum: Optional[int],
    maximum: Optional[int],
    currency: Optional[str],
    converter: CurrencyConverter,
) -> SalaryBand:
    """Normalize salary amounts to the converter's base currency."""

    return SalaryBand(
        min=converter.convert(minimum, currency),
        max=converter.convert(maximum, currency),
    )


def match_location(preference: LocationPreference, job_location: JobLocation) -> Tuple[float, List[str]]:
    """Return location fit score and rationale fragments."""

    reasons: List[str] = []
    job_modes = {
        mode: getattr(job_location, mode)
        for mode in ("remote", "hybrid", "onsite")
        if getattr(job_location, mode) is not None
    }
    pref_modes = {"remote": preference.remote, "hybrid": preference.hybrid, "onsite": preference.onsite}
    mode_match = any(job_modes.get(mode, False) and pref_modes[mode] for mode in pref_modes)

    city_match = job_location.city and job_location.city in preference.cities
    country_match = job_location.country and job_location.country in preference.countries

    if mode_match:
        reasons.append("Work modality aligns")
    elif job_location.remote and preference.remote:
        mode_match = True
        reasons.append("Remote acceptable")

    geo_match = False
    if city_match:
        geo_match = True
        reasons.append(f"City preference matched {job_location.city}")
    elif country_match:
        geo_match = True
        reasons.append(f"Country preference matched {job_location.country}")
    elif preference.relocation:
        geo_match = True
        reasons.append("User open to relocation")

    score = 0.0
    if mode_match:
        score += 0.5
    if geo_match:
        score += 0.5
    return score, reasons
