from enum import Enum
import logging

from pydantic import BaseModel
import yaml

logger = logging.getLogger(__name__)


class ReliabilityTier(str, Enum):
    authoritative = "authoritative"
    reference = "reference"
    supplementary = "supplementary"


class SourceEntry(BaseModel):
    name: str
    domain: str
    category: str
    base_url: str | None = None
    search_url_pattern: str | None = None
    requires_auth: bool = False
    reliability_tier: ReliabilityTier = ReliabilityTier.reference
    notes: str | None = None


class SourceRegistry(BaseModel):
    guidelines: list[SourceEntry] = []
    textbooks: list[SourceEntry] = []
    journals: list[SourceEntry] = []
    formularies: list[SourceEntry] = []

    @property
    def all_sources(self) -> list[SourceEntry]:
        return self.guidelines + self.textbooks + self.journals + self.formularies


def load_source_registry(path: str) -> SourceRegistry:
    """Load and validate source registry. Warn on bad entries, load valid ones (D-29)."""
    with open(path) as f:
        raw = yaml.safe_load(f)
    if not raw:
        logger.warning("Source registry file is empty: %s", path)
        return SourceRegistry()
    if not isinstance(raw, dict):
        logger.warning("Source registry is not a mapping (got %s): %s", type(raw).__name__, path)
        return SourceRegistry()
    validated = {}
    for category in ["guidelines", "textbooks", "journals", "formularies"]:
        entries = []
        raw_category = raw.get(category, [])
        if not isinstance(raw_category, (list, tuple)):
            logger.warning(
                "Skipping category %s: expected a list, got %s",
                category,
                type(raw_category).__name__,
            )
            continue
        for item in raw_category:
            if not isinstance(item, dict):
                logger.warning(
                    "Skipping non-mapping entry in %s: %r", category, item
                )
                continue
            try:
                entries.append(SourceEntry(category=category, **item))
            except Exception as e:
                logger.warning(
                    "Skipping invalid source entry in %s: %s - %s",
                    category,
                    item.get("name", "unknown"),
                    e,
                )
        validated[category] = entries
    return SourceRegistry(**validated)
