"""Tests for the trusted source registry YAML loader."""

import tempfile

from app.sources.registry import SourceRegistry, load_source_registry


def test_load_source_registry_returns_sources():
    """Loading config/sources.yml returns a SourceRegistry with sources."""
    registry = load_source_registry("config/sources.yml")
    assert isinstance(registry, SourceRegistry)
    assert len(registry.all_sources) > 0, "Registry should have at least one source"


def test_registry_contains_cps():
    """Registry contains CPS (cps.ca) as a trusted source."""
    registry = load_source_registry("config/sources.yml")
    domains = [s.domain for s in registry.all_sources]
    assert "cps.ca" in domains, "Registry should contain cps.ca"


def test_all_sources_have_required_fields():
    """Every source has non-empty name and domain."""
    registry = load_source_registry("config/sources.yml")
    for source in registry.all_sources:
        assert source.name, f"Source missing name: {source}"
        assert source.domain, f"Source missing domain: {source}"


def test_all_sources_have_valid_reliability_tier():
    """Every source has a valid reliability_tier value."""
    registry = load_source_registry("config/sources.yml")
    valid_tiers = {"authoritative", "reference", "supplementary"}
    for source in registry.all_sources:
        assert source.reliability_tier.value in valid_tiers, (
            f"Invalid tier for {source.name}: {source.reliability_tier}"
        )


def test_invalid_entry_skipped_valid_loaded():
    """Invalid YAML entry is skipped, valid entries still load."""
    yaml_content = """
guidelines:
  - name: Valid Source
    domain: valid.com
    base_url: https://valid.com
    reliability_tier: authoritative
  - name: 123
    domain_typo: bad.com
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(yaml_content)
        f.flush()
        registry = load_source_registry(f.name)

    assert len(registry.guidelines) == 1, "Should load the one valid entry"
    assert registry.guidelines[0].domain == "valid.com"
