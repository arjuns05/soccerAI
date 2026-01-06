from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    # Kafka
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic_match_events: str = os.getenv("TOPIC_MATCH_EVENTS", "match_events")
    topic_player_events: str = os.getenv("TOPIC_PLAYER_EVENTS", "player_events")
    topic_predictions: str = os.getenv("TOPIC_PREDICTIONS", "match_predictions")
    consumer_group: str = os.getenv("CONSUMER_GROUP", "fantasy_ai_group")

    # Postgres
    pg_host: str = os.getenv("PG_HOST", "localhost")
    pg_port: int = int(os.getenv("PG_PORT", "5433"))
    pg_db: str = os.getenv("PG_DB", "fantasy_ai")
    pg_user: str = os.getenv("PG_USER", "postgres")
    pg_password: str = os.getenv("PG_PASSWORD", "postgres")

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")


    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_text_model: str = os.getenv("OPENAI_TEXT_MODEL", "gpt-5.2")
    openai_embed_model: str = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")


    rag_top_k: int = int(os.getenv("RAG_TOP_K", "5"))

    # Prediction cadence
    predict_every_n_events: int = int(os.getenv("PREDICT_EVERY_N_EVENTS", "25"))

settings = Settings()
