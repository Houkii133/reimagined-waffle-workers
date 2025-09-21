"""Text understanding and feature extraction."""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .data_models import JobPosting, UserProfile
from .normalization import OntologyNormalizer, scrub_pii

TOKEN_RE = re.compile(r"[A-Za-z0-9+#.]+")


@dataclass
class LanguageDetector:
    """Very light language detection stub.

    The detector computes a hash of the text and deterministically returns
    ``"en"`` for ASCII-dominant text and ``"other"`` otherwise. This keeps
    the pipeline deterministic and dependency-free.
    """

    threshold: float = 0.7

    def detect(self, text: str) -> str:
        if not text:
            return "unknown"
        ascii_chars = sum(1 for ch in text if ord(ch) < 128)
        ratio = ascii_chars / max(len(text), 1)
        return "en" if ratio >= self.threshold else "other"


@dataclass
class EmbeddingProvider:
    """Interface for embedding computation."""

    dim: int = 128

    def embed(self, text: str) -> List[float]:  # pragma: no cover - override in subclasses
        raise NotImplementedError


@dataclass
class HashingEmbeddingProvider(EmbeddingProvider):
    """Deterministic hashing embeddings for offline tests."""

    dim: int = 128

    def embed(self, text: str) -> List[float]:
        tokens = TOKEN_RE.findall(text.lower())
        vector = [0.0] * self.dim
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            digest_len = len(digest)
            for i in range(self.dim):
                vector[i] += digest[i % digest_len] / 255.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


@dataclass
class TextPreprocessor:
    """Prepare text for downstream feature extraction."""

    language_detector: LanguageDetector = field(default_factory=LanguageDetector)

    def preprocess(self, text: str) -> str:
        detected = self.language_detector.detect(text)
        cleaned = scrub_pii(text.lower())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if detected != "en":
            cleaned = f"[{detected}] {cleaned}"
        return cleaned


def extract_keywords(text: str, top_k: int = 10) -> List[str]:
    tokens = TOKEN_RE.findall(text.lower())
    counts = Counter(tokens)
    return [token for token, _ in counts.most_common(top_k)]


def infer_soft_skills(text: str, ontology: OntologyNormalizer) -> List[str]:
    matches = []
    for raw, canonical in ontology.ontology.soft_skills.items():
        if raw in text:
            matches.append(canonical)
    return sorted(set(matches))


def tag_skills(tokens: Sequence[str], ontology: OntologyNormalizer) -> List[str]:
    found: List[str] = []
    for token in tokens:
        canonical = ontology.ontology.skills.get(token.lower())
        if canonical:
            found.append(canonical)
    return sorted(set(found))


def detect_seniority(text: str, ontology: OntologyNormalizer) -> str:
    for raw, canonical in ontology.ontology.seniority.items():
        if raw in text.lower():
            return canonical
    return "mid"


def detect_must_have_phrases(text: str) -> List[str]:
    patterns = ["must have", "required", "need to", "strong experience"]
    sentences = re.split(r"[.!]", text.lower())
    musts = []
    for sentence in sentences:
        if any(phrase in sentence for phrase in patterns):
            musts.append(sentence.strip())
    return musts


@dataclass
class FeatureExtractor:
    """Extract structured signals from text."""

    ontology: OntologyNormalizer
    embedder: EmbeddingProvider
    preprocessor: TextPreprocessor = field(default_factory=TextPreprocessor)

    def process_job(self, job: JobPosting) -> Dict[str, object]:
        text = " ".join(
            [job.title, job.description, " ".join(job.requirements), " ".join(job.responsibilities)]
        )
        clean_text = self.preprocessor.preprocess(text)
        tokens = TOKEN_RE.findall(clean_text)
        keywords = extract_keywords(clean_text)
        hard_skills = sorted(
            set(tag_skills(tokens, self.ontology)).union(self.ontology.normalize_skills(job.skills))
        )
        soft_skills = infer_soft_skills(clean_text, self.ontology)
        seniority = self.ontology.normalize_seniority(job.seniority or detect_seniority(clean_text, self.ontology))
        must_haves = detect_must_have_phrases(clean_text)
        embedding = self.embedder.embed(clean_text)
        return {
            "keywords": keywords,
            "hard_skills": hard_skills,
            "soft_skills": soft_skills,
            "seniority": seniority,
            "must_haves": must_haves,
            "embedding": embedding,
        }

    def process_user(self, user: UserProfile) -> Dict[str, object]:
        profile_text = " ".join(
            [
                " ".join(user.roles_history),
                user.career_goals,
                " ".join(user.desired_roles),
            ]
        )
        clean_text = self.preprocessor.preprocess(profile_text)
        embedding = self.embedder.embed(clean_text)
        keywords = extract_keywords(clean_text)
        soft_skills = self.ontology.normalize_soft_skills(user.soft_skills)
        hard_skills = self.ontology.normalize_skills(user.hard_skills)
        return {
            "keywords": keywords,
            "soft_skills": soft_skills,
            "hard_skills": hard_skills,
            "embedding": embedding,
        }


def cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))
