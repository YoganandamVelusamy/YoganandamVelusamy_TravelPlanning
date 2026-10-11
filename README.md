# AI-Powered Travel Planning & Itinerary Assistant

Local-first capstone project for retrieving similar travel experiences and ranking destinations and activities from historical travel data.

## Problem Statement

Travel professionals often search historical reviews and ratings manually to find experiences similar to a traveler's interests, destination preferences, rating expectations, and travel party. This is slow and makes it difficult to compare relevant destinations consistently.

## Business Objective

Reduce the time needed to find comparable travel experiences and help travel professionals make more consistent, evidence-informed destination and activity recommendations.

## Project Overview

This is a local-first capstone microservice for travel-experience retrieval and trip recommendation. Users enter a natural-language trip description, refine it with filters, and review ranked destination/activity results with the matching experience records.

## Solution Summary

The application validates and normalizes the provided CSV data, converts each enriched row into a retrieval document, combines keyword and vector retrieval with Reciprocal Rank Fusion, extracts supported preferences, and ranks destinations and activity categories. FastAPI exposes the functionality; Streamlit provides the user interface; feedback is stored separately in SQLite.

## Current implementation

- CSV normalization and validation, including in-memory normalization of the source header `roverall_rating` to the API field `overall_rating`.
- Semantic embeddings from `sentence-transformers/all-MiniLM-L6-v2` by default, persistent local Chroma vector storage, BM25 keyword ranking, and Reciprocal Rank Fusion. An explicit `EMBEDDING_BACKEND=tfidf` offline fallback uses local TF-IDF vectors and is identified by the health endpoint.
- Deterministic preference extraction and destination/activity prioritization.
- FastAPI endpoints for health, search, recommendations, itinerary feasibility disclosure, and feedback capture.
- Streamlit travel studio UI with a local coastal hero image, responsive styling, an animated flight-symbol loading screen, query filters, evidence, and feedback.
- Unit and API tests for the current implementation.

LLM generation, LLM-as-judge execution, DeepEval reports, learned feedback reranking, and a day-by-day itinerary scheduler are not implemented yet. Recommendation and feasibility outputs are deterministic and do not claim those features.

## Data and provenance

The workspace contains three related CSVs:

- `data/sample_data.csv`: raw user-by-category rating matrix with generic `Category 1` through `Category 24` names.
- `data/column_names_changed.csv`: same rating matrix with descriptive activity-category names.
- `data/modified_data.csv`: renamed activity ratings plus destination, visited categories, overall rating, review text, travel type, and visit date.

The latter fields do not exist in the rating-only CSVs. Treat the added review text and travel metadata as synthetic/unverified enrichment, not authentic TripAdvisor reviews. The source link in the project brief also appears inconsistent with its described review dataset; verify provenance before external publication. The application marks enriched records and includes this limitation in recommendation responses.

## Technology Stack

| Requirement | Current implementation |
|---|---|
| Programming Language | Python 3.11+ (validated in Python 3.13) |
| LLM Used | None. Current recommendations are deterministic; no LLM provider is called. |
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` by default; optional local TF-IDF vector fallback via `EMBEDDING_BACKEND=tfidf` |
| Vector Database | Chroma, persisted under `data/vector_db/` |
| Frameworks Used | FastAPI, Pydantic, Uvicorn, Streamlit |
| Retrieval | BM25 keywords + vector similarity, fused with Reciprocal Rank Fusion |
| Feedback storage | SQLite, separate from source CSV files |

LLM generation, LLM-as-judge, and DeepEval evaluation are planned capabilities, not part of the current runtime. No LLM name or evaluation score is claimed for this implementation.

## Installation Instructions

### Environment Setup

Use Python 3.11 or newer from the repository root. Create and activate a virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Dependency Installation

Install the project dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

The first API startup downloads the configured embedding model if it is not already cached. If model hosting is unreachable, set `EMBEDDING_BACKEND=tfidf` in `.env`; this stays local and keeps vector-plus-keyword retrieval available, but TF-IDF is less capable than transformer embeddings for paraphrase matching.

### API Key Configuration

No API key is needed for the current search, recommendation, or feedback features. `OPENAI_API_KEY` and `OPENAI_MODEL` appear in `.env.example` only as placeholders for possible future LLM features; the current application does not read or call that provider. Do not add real secrets to source control.

## Local Deployment Instructions

Start the API in one terminal:

```powershell
uvicorn src.main:app --reload
```

Start the UI in another terminal:

```powershell
streamlit run frontend.py
```

Open the Streamlit URL printed by the command. FastAPI's interactive API docs are at `http://127.0.0.1:8000/docs`; health is at `http://127.0.0.1:8000/health`.

Environment overrides are available in `.env.example`: dataset path, vector database path, feedback database path, embedding model, and API base URL.

## Sample Queries and Expected Outputs

Exact rankings can vary with the selected embedding backend and corpus. These examples describe the expected response behavior, not guaranteed destination rankings.

1. **Query:** `A beach trip with local food for a couple`

  **Expected:** The preference profile includes `beaches`, `restaurants`, and `Couple`; the response contains matching experience evidence and ranked destination/activity summaries.

2. **Query:** `A family city break with museums and parks`

  **Expected:** The preference profile identifies `Family`, `museums`, and `parks`; matching historical cases are returned with ranked destinations and activity ratings.

3. **Query:** `5-day trip by the coast with cafes`

  **Expected:** The preference profile captures a five-day duration and the coastal/beach and cafe interests when matched by the classifier; recommendations include evidence IDs and historical ratings.

4. **Query:** `Plan a 5-day beach trip under $900`

  **Expected:** The recommendation response captures the beach interest, five-day duration, and budget amount. A request to `/api/v1/itinerary/feasibility` returns `insufficient_data`, because the supplied dataset has no activity-duration or price fields; it does not claim the trip is feasible.

Use these natural-language examples in the Streamlit query box. API requests can also be sent to `POST /api/v1/recommendations` and `POST /api/v1/itinerary/feasibility` as documented below.

## API examples

Search similar experiences:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/search `
  -ContentType 'application/json' `
  -Body '{"query":"beach trip with local food","limit":5,"filters":{"min_rating":2.5}}'
```

Get ranked recommendations:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/recommendations `
  -ContentType 'application/json' `
  -Body '{"query":"5-day beach trip with local food for a couple","limit":5}'
```

Expected response shape includes a preference profile, destination/activity summaries, retrieved evidence IDs and review text, hybrid scores, and limitations. Exact results depend on the local dataset and embedding model. Since price and activity-duration fields are absent, itinerary feasibility requests explicitly return `insufficient_data` when those constraints are supplied.

Other endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Dataset/service status |
| POST | `/api/v1/search` | Hybrid experience retrieval with metadata filters |
| POST | `/api/v1/recommendations` | Preference classification and ranked summaries |
| POST | `/api/v1/itinerary/feasibility` | Feasibility assessment and evidence; reports missing cost/duration data |
| POST | `/api/v1/feedback` | Save a 1–5 feedback rating to SQLite |

## Tests

```powershell
python -m unittest discover -v
```

The tests use deterministic embedding doubles; running the test suite does not download the embedding model or need an API key.

## Planned capstone work

Next stages: optional LLM synthesis and LLM-as-judge, DeepEval query set/report, explicit itinerary suitability scoring, opt-in feedback reranking, architecture/design/API/dataset documents, a polished evaluation artifact, and the 10-minute presentation package. Generated or unknown fields must remain clearly identified as such throughout those deliverables.