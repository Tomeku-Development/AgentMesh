"""Property-based tests for webhook HTTPS URL validation.

**Feature: saas-platform-enhancements, Property 3: Webhook HTTPS URL validation**
**Validates: Requirements 2.6**
"""

from __future__ import annotations

import string

from hypothesis import given, settings, strategies as st
from pydantic import ValidationError

from mesh_platform.schemas.webhook import WebhookCreate

# ---------------------------------------------------------------------------
# Helpers — fixed valid values for non-URL fields so we isolate URL validation
# ---------------------------------------------------------------------------

VALID_EVENT_TYPES = ["order.request"]
VALID_SECRET = "test-hmac-secret"


def build_webhook(url: str) -> WebhookCreate:
    """Attempt to construct a WebhookCreate with the given URL.

    Uses fixed valid values for event_types and secret so that only the URL
    field is under test.
    """
    return WebhookCreate(url=url, event_types=VALID_EVENT_TYPES, secret=VALID_SECRET)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Strategy: generate plausible HTTPS URLs
_path_chars = string.ascii_letters + string.digits + "-._~:/?#[]@!$&'()*+,;="
https_urls = st.builds(
    lambda domain, path: f"https://{domain}/{path}",
    domain=st.from_regex(r"[a-z][a-z0-9\-]{0,20}\.[a-z]{2,6}", fullmatch=True),
    path=st.text(alphabet=_path_chars, min_size=0, max_size=60),
)

# Strategy: non-HTTPS protocol URLs
_non_https_schemes = ["http://", "ftp://", "ws://", "wss://", "file://", "ssh://", "tcp://"]
non_https_urls = st.builds(
    lambda scheme, domain, path: f"{scheme}{domain}/{path}",
    scheme=st.sampled_from(_non_https_schemes),
    domain=st.from_regex(r"[a-z][a-z0-9\-]{0,20}\.[a-z]{2,6}", fullmatch=True),
    path=st.text(alphabet=_path_chars, min_size=0, max_size=60),
)

# Strategy: random strings that are unlikely to be valid URLs
random_non_url_strings = st.text(
    alphabet=st.characters(categories=("L", "N", "P", "S", "Z")),
    min_size=0,
    max_size=100,
).filter(lambda s: not s.startswith("https://"))


# ---------------------------------------------------------------------------
# Property 3 — Webhook HTTPS URL validation
# ---------------------------------------------------------------------------


class TestWebhookHTTPSURLValidation:
    """Property 3: Webhook HTTPS URL validation.

    *For any* URL string, webhook registration SHALL succeed only if the URL
    starts with ``https://``, and SHALL reject all URLs using other protocols
    (http, ftp, ws, etc.).

    **Validates: Requirements 2.6**
    """

    @given(url=https_urls)
    @settings(max_examples=100)
    def test_https_urls_are_accepted(self, url: str) -> None:
        """Any URL starting with https:// SHALL be accepted by WebhookCreate."""
        webhook = build_webhook(url)
        assert webhook.url == url, (
            f"WebhookCreate should accept HTTPS URL '{url}' and preserve it"
        )

    @given(url=non_https_urls)
    @settings(max_examples=100)
    def test_non_https_protocol_urls_are_rejected(self, url: str) -> None:
        """URLs using http://, ftp://, ws://, etc. SHALL be rejected."""
        try:
            build_webhook(url)
            raise AssertionError(
                f"WebhookCreate should reject non-HTTPS URL '{url}' "
                f"but it was accepted"
            )
        except ValidationError:
            pass  # expected — validation correctly rejected the URL

    @given(url=random_non_url_strings)
    @settings(max_examples=100)
    def test_random_non_url_strings_are_rejected(self, url: str) -> None:
        """Random strings that don't start with https:// SHALL be rejected."""
        try:
            build_webhook(url)
            raise AssertionError(
                f"WebhookCreate should reject non-URL string '{url!r}' "
                f"but it was accepted"
            )
        except ValidationError:
            pass  # expected — validation correctly rejected the string

    @given(url=st.text(min_size=0, max_size=200))
    @settings(max_examples=100)
    def test_acceptance_iff_starts_with_https(self, url: str) -> None:
        """For any string: accepted ⟺ starts with 'https://'."""
        starts_with_https = url.startswith("https://")
        try:
            webhook = build_webhook(url)
            accepted = True
        except ValidationError:
            accepted = False

        if starts_with_https:
            assert accepted is True, (
                f"URL '{url}' starts with 'https://' so it should be accepted"
            )
        else:
            assert accepted is False, (
                f"URL '{url}' does NOT start with 'https://' so it should be rejected"
            )
