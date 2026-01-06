# Fantasy Soccer AI Engine (Real-Time Match Prediction + RAG Explanations)

## Overview
This project is a real-time football (UEFA-style) prediction engine that:
- Streams match and player events through Kafka
- Maintains low-latency match state in Redis
- Stores events, predictions, and retrieval documents in PostgreSQL
- Uses an XGBoost classifier to predict match outcomes (HOME_WIN / DRAW / AWAY_WIN)
- Produces explainable rationales via Retrieval-Augmented Generation (RAG) using a Llama-family model through a third-party API (no OpenAI dependency)

A built-in simulator generates events so you can run the system end-to-end without external data feeds.

## Architecture

### Components
- Kafka: event bus
  - `match_events`: match-level events (kickoff, shot, goal, foul, corner)
  - `player_events`: player-level events (player stat updates)
  - `match_predictions`: model outputs (probabilities + explanation)
- Redis: low-latency state/cache
  - `match_state:<match_id>`: rolling match state (score, xG, shots, etc.)
  - `match_pred:<match_id>`: latest prediction payload
- PostgreSQL: durable storage
  - `matches`: match metadata
  - `match_events`, `player_events`: raw event logs
  - `predictions`: prediction history (probabilities, features, explanation)
  - `rag_docs`: documents used for retrieval (synthetic historical match snippets)
- Model
  - XGBoost multiclass classifier
- RAG
  - Local embeddings (HashingVectorizer) for retrieval (no paid embedding API)
  - Llama-family chat model via OpenRouter (or another OpenAI-compatible gateway) for explanation synthesis

### Data Flow
1. `producer_simulator` publishes match/player events to Kafka
2. `consumer_predictor` consumes events:
   - updates match state in Redis
   - writes raw events to Postgres
   - every N events builds features and runs XGBoost
   - retrieves top-k similar historical docs from Postgres (RAG)
   - calls LLM to write an explanation grounded in retrieved docs
   - writes prediction row to Postgres
   - publishes prediction JSON to `match_predictions`
   - caches latest prediction in Redis

## Repository Layout (key files)
- `app/`
  - `kafka_io.py`: Kafka producer/consumer utilities (confluent-kafka)
  - `db.py`: SQLAlchemy engine/session + Base
  - `models.py`: SQLAlchemy models
  - `features.py`: state -> feature vector
  - `xgb_model.py`: train/load/predict helpers
  - `rag_explain.py`: retrieval + explanation generation
  - `llm_client.py`: LLM API client (OpenRouter/OpenAI-compatible)
  - `redis_cache.py`: Redis helpers
- `scripts/`
  - `bootstrap_db.py`: creates DB (if missing) and tables
  - `create_topics.py`: creates Kafka topics (if broker allows)
  - `build_rag_store.py`: seeds `rag_docs` and embeddings
  - `train_xgb.py`: trains and saves model artifact
  - `consumer_predictor.py`: main engine loop
  - `producer_simulator.py`: event simulator
  - `api_server.py`: optional FastAPI to query latest predictions
  - `test_llm.py`, `test_rag.py`, `test_explain.py`: optional sanity tests

## Requirements

### Software
- Python 3.11+ recommended (3.12 is a good target). Python 3.13 may work but some libraries are still catching up.
- PostgreSQL 14+
- Redis 6+
- Kafka broker (KRaft mode supported)

### Python dependencies
At minimum:
- `SQLAlchemy>=2.0`
- `psycopg[binary]` (psycopg v3)
- `redis`
- `confluent-kafka`
- `scikit-learn`
- `xgboost`
- `requests`
- `fastapi` + `uvicorn` (optional API)

## Configuration

Create a `.env` file in the project root.

### Example `.env`
```env
# Postgres
PG_HOST=127.0.0.1
PG_PORT=5432
PG_DB=fantasy_ai
PG_USER=postgres
PG_PASSWORD=postgres

# Redis
REDIS_URL=redis://127.0.0.1:6379/0

# Kafka (use 127.0.0.1 to avoid IPv6 ::1 issues)
KAFKA_BOOTSTRAP_SERVERS=127.0.0.1:9092
TOPIC_MATCH_EVENTS=match_events
TOPIC_PLAYER_EVENTS=player_events
TOPIC_PREDICTIONS=match_predictions
CONSUMER_GROUP=fantasy_ai_engine

# Prediction cadence
PREDICT_EVERY_N_EVENTS=10
RAG_TOP_K=3

# LLM (OpenRouter example; no OpenAI dependency)
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=YOUR_KEY_HERE
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free


Execution Test: 
Run: python -m scripts.test_explain
This will walk you through one example of a full explanation of produced outputs