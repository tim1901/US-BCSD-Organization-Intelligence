from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "production"
    app_name: str = "us-bcsd-organizational-intelligence"
    log_level: str = "INFO"
    port: int = 10000
    organization_timezone: str = "America/Chicago"

    database_url: str = Field(default="", alias="DATABASE_URL")
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(default="", alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_storage_bucket: str = Field(default="us-bcsd-sources", alias="SUPABASE_STORAGE_BUCKET")

    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_fast_model: str = Field(default="gemini-3.1-flash-lite", alias="GEMINI_FAST_MODEL")
    gemini_brain_model: str = Field(default="gemini-3.8-flash", alias="GEMINI_BRAIN_MODEL")
    gemini_research_model: str = Field(default="gemini-3.8-flash", alias="GEMINI_RESEARCH_MODEL")
    gemini_embedding_model: str = Field(default="gemini-embedding-001", alias="GEMINI_EMBEDDING_MODEL")
    gemini_embedding_dimensions: int = Field(default=3072, alias="GEMINI_EMBEDDING_DIMENSIONS")

    slack_bot_token: str = Field(default="", alias="SLACK_BOT_TOKEN")
    slack_signing_secret: str = Field(default="", alias="SLACK_SIGNING_SECRET")
    slack_app_token: str = Field(default="", alias="SLACK_APP_TOKEN")
    slack_workspace_id: str = Field(default="", alias="SLACK_WORKSPACE_ID")
    slack_workspace_name: str = Field(default="", alias="SLACK_WORKSPACE_NAME")

    max_slack_event_age_seconds: int = Field(default=300, alias="MAX_SLACK_EVENT_AGE_SECONDS")
    max_request_body_bytes: int = Field(default=1_000_000, alias="MAX_REQUEST_BODY_BYTES")
    max_upload_bytes: int = Field(default=25_000_000, alias="MAX_UPLOAD_BYTES")
    worker_poll_seconds: float = Field(default=2.0, alias="WORKER_POLL_SECONDS")
    worker_batch_size: int = Field(default=10, alias="WORKER_BATCH_SIZE")
    job_max_attempts: int = Field(default=5, alias="JOB_MAX_ATTEMPTS")

    research_max_seconds: int = Field(default=300, alias="RESEARCH_MAX_SECONDS")
    research_max_iterations: int = Field(default=8, alias="RESEARCH_MAX_ITERATIONS")
    research_max_sources: int = Field(default=30, alias="RESEARCH_MAX_SOURCES")
    research_max_model_calls: int = Field(default=30, alias="RESEARCH_MAX_MODEL_CALLS")
    research_max_output_tokens: int = Field(default=12_000, alias="RESEARCH_MAX_OUTPUT_TOKENS")
    research_max_cost_usd: float = Field(default=5.0, alias="RESEARCH_MAX_COST_USD")
    search_monthly_ceiling: int = Field(default=4500, alias="SEARCH_MONTHLY_CEILING")

    model_config = SettingsConfigDict(env_file='.env', extra='ignore', populate_by_name=True)

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
