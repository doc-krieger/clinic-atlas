from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://clinic_atlas:clinic_atlas_dev@localhost:5432/clinic_atlas"

    # Data paths (D-25)
    clinic_atlas_notes_dir: str = "/data/notes"
    clinic_atlas_sources_dir: str = "/data/sources"
    clinic_atlas_sources_file: str = "/config/sources.yml"

    # LLM (D-32)
    ollama_base_url: str = "http://ollama:11434"
    llama_server_url: str | None = None  # Optional alternative (D-32)

    # SearXNG
    searxng_url: str = "http://searxng:8080"

    # API
    api_prefix: str = "/api"  # D-39: no versioning

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
