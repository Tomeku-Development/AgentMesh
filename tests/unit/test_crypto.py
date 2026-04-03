"""Tests for HMAC-SHA256 crypto module."""

import pytest
from datetime import datetime, timezone, timedelta
from mesh.core.crypto import (
    canonical_json,
    sign_message,
    verify_signature,
    is_message_fresh,
    ReplayDetector,
)


class TestCanonicalJson:
    def test_sorted_keys(self):
        result = canonical_json({"z": 1, "a": 2, "m": 3})
        assert result == '{"a":2,"m":3,"z":1}'

    def test_no_whitespace(self):
        result = canonical_json({"key": "value"})
        assert " " not in result

    def test_deterministic(self):
        data = {"b": [1, 2], "a": {"nested": True}}
        assert canonical_json(data) == canonical_json(data)


class TestSignVerify:
    def test_sign_returns_hex_string(self):
        sig = sign_message({"test": "data"})
        assert len(sig) == 64  # SHA-256 hex digest
        int(sig, 16)  # Should be valid hex

    def test_verify_valid_signature(self):
        data = {"order_id": "123", "price": 99.5}
        sig = sign_message(data)
        assert verify_signature(data, sig)

    def test_verify_fails_on_tampered_data(self):
        data = {"order_id": "123", "price": 99.5}
        sig = sign_message(data)
        assert not verify_signature({"order_id": "123", "price": 100.0}, sig)

    def test_verify_fails_on_wrong_secret(self):
        data = {"test": "data"}
        sig = sign_message(data, b"secret1")
        assert not verify_signature(data, sig, b"secret2")

    def test_sign_with_custom_secret(self):
        data = {"test": "data"}
        sig1 = sign_message(data, b"secret_a")
        sig2 = sign_message(data, b"secret_b")
        assert sig1 != sig2


class TestMessageFreshness:
    def test_fresh_message(self):
        now = datetime.now(timezone.utc).isoformat()
        assert is_message_fresh(now)

    def test_stale_message(self):
        old = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
        assert not is_message_fresh(old, max_age=60)

    def test_invalid_timestamp(self):
        assert not is_message_fresh("not-a-date")

    def test_empty_timestamp(self):
        assert not is_message_fresh("")


class TestReplayDetector:
    def test_new_nonce_accepted(self):
        rd = ReplayDetector()
        assert rd.check_and_record("nonce_1")

    def test_duplicate_nonce_rejected(self):
        rd = ReplayDetector()
        rd.check_and_record("nonce_1")
        assert not rd.check_and_record("nonce_1")

    def test_different_nonces_accepted(self):
        rd = ReplayDetector()
        assert rd.check_and_record("a")
        assert rd.check_and_record("b")
        assert rd.check_and_record("c")

    def test_eviction_on_overflow(self):
        rd = ReplayDetector(max_size=10)
        for i in range(15):
            rd.check_and_record(f"nonce_{i}")
        # Old nonces should be evicted, new ones should work
        assert rd.check_and_record("fresh_nonce")
