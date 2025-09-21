# JobMatch Intelligence Engine

This repository implements the **core intelligence** for an ARIF-governed job matching platform. It focuses on high quality ranking, explainability, continuous learning from feedback, and fairness telemetry. The code is framework-agnostic and can be embedded in services or batch workflows.

## Features

- Typed data contracts for user profiles, job postings, recommendations, and feedback.
- Ontology-driven normalization with configurable synonym maps for skills, roles, industries, and seniority.
- Provider-agnostic embedding layer (deterministic hashing implementation included) with text preprocessing, skill tagging, and soft-skill inference.
- Hybrid ranking algorithm combining symbolic filters with learned similarity components, rationale generation, and qualification gap suggestions.
- Online feedback learner that personalizes weights and updates a lightweight propensity model.
- Explainability utilities (`why_not`, `what_if`), telemetry snapshots, and fairness hooks.
- Offline metrics (Precision@K, nDCG, Coverage, Diversity, MRR) and synthetic dataset generator for reproducible testing.

## Installation

This project targets Python 3.10+. Install dependencies for testing:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # optional if you add external deps
pip install pytest pyyaml
```

> The engine itself only relies on the Python standard library and PyYAML.

## Usage Example

```python
from jobmatch.engine import JobMatchEngine
from jobmatch.nlp import HashingEmbeddingProvider

engine = JobMatchEngine(embedding_provider=HashingEmbeddingProvider(dim=64))
users, jobs = engine.load_synthetic(users=3, jobs=50)

# Ingest additional jobs if needed
# engine.ingest_jobs(custom_jobs)

user = users[0]
recommendations = engine.recommend(user, top_k=5)
for rec in recommendations:
    print(rec.job_id, rec.score, rec.rationale, rec.qualification_gaps)

feedback = Feedback(
    user_id=user.user_id,
    job_id=recommendations[0].job_id,
    signal_type="apply",
    value=None,
    timestamp=datetime.utcnow(),
)
engine.record_feedback(feedback)

# Counterfactual analysis
improved = engine.what_if(user, {"add_skills": ["Kubernetes"]})
print("New top job after upskilling:", improved[0].job_id)
```

### Worked Example

Running the snippet above on the synthetic dataset yields output similar to:

```
job-14 0.78 ['Matches 3 hard skills', 'Soft skills alignment: communication, ownership'] ['Upskill: Docker']
job-07 0.75 ['Work modality aligns', 'Growth: manager_track'] ['Upskill: Kubernetes']
...
```

If the user adds `Kubernetes` via `what_if`, the top match typically shifts toward platform-oriented roles, demonstrating explainability and controllable upskilling guidance.

## Testing

Execute the automated tests:

```bash
pytest
```

All tests use deterministic seeds and the in-memory synthetic dataset for reproducible results.

## Project Layout

```
jobmatch/
  __init__.py
  data_models.py          # Data contracts
  normalization.py        # Ontology normalization and salary utilities
  nlp.py                  # Text preprocessing, embeddings, feature extraction
  scoring.py              # Hybrid scoring components and rationale builder
  engine.py               # JobMatchEngine orchestrating the workflow
  learning.py             # Feedback learner and propensity model
  metrics.py              # Offline evaluation metrics
  datasets.py             # Synthetic dataset generator
  config/
    default_weights.yaml
    skill_synonyms.yaml
```

## Governance Notes

- The engine never uses protected attributes and scrubs basic PII in text fields.
- `Telemetry` exposes filter counters to support bias audits.
- Weight customization through feedback adheres to ARIF guidance by surfacing rationale and trade-offs whenever constraints block matches.

## License

This project is provided as-is for demonstration and extension within your environment.
