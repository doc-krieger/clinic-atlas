import pytest


class TestSearxngSearch:
    @pytest.mark.xfail(reason="Awaiting SearXNG client implementation (Plan 02)")
    def test_search_returns_filtered_results(self):
        """SRCI-05: Search returns results filtered to trusted domains."""
        assert False, "Not yet implemented"

    @pytest.mark.xfail(reason="Awaiting SearXNG client implementation (Plan 02)")
    def test_domain_post_filtering(self):
        """D-11: Results post-filtered to trusted domains only."""
        assert False, "Not yet implemented"
