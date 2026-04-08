from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = (
        "postgresql://clinic_atlas:clinic_atlas_dev@localhost:5432/clinic_atlas"
    )

    # Data paths (D-25)
    clinic_atlas_notes_dir: str = "/data/notes"
    clinic_atlas_sources_dir: str = "/data/sources"
    clinic_atlas_sources_file: str = "/config/sources.yml"

    # LLM (D-32)
    ollama_base_url: str = "http://ollama:11434"
    llama_server_url: str = ""  # Optional alternative (D-32)

    # SearXNG
    searxng_url: str = "http://searxng:8080"

    # API
    api_prefix: str = "/api"  # D-39: no versioning

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Source ingestion (Phase 2)
    max_upload_size_mb: int = Field(default=50, ge=1)  # D-03: 50 MB file size limit
    docling_ocr_enabled: bool = False  # D-06: OCR disabled by default
    httpx_timeout: float = Field(default=30.0, gt=0)  # URL fetch timeout
    playwright_timeout: int = Field(default=30000, ge=1000)  # Playwright page.goto timeout (ms)
    max_response_size_mb: int = Field(default=20, ge=1)  # Max response size for URL fetch
    max_redirects: int = Field(default=5, ge=1)  # Redirect cap for SSRF protection

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
