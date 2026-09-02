import pytest
from datetime import timedelta

from app.core import security


def test_password_hash_roundtrip():
    hashed = security.hash_password("S3curePassw0rd!")
    assert hashed != "S3curePassw0rd!"
    assert hashed.startswith("$2")  # bcrypt-format hash
    assert security.verify_password("S3curePassw0rd!", hashed)


def test_password_verify_rejects_wrong_password():
    hashed = security.hash_password("correct-horse")
    assert security.verify_password("wrong-battery", hashed) is False


def test_password_verify_survives_corrupt_hash():
    assert security.verify_password("x", "not-a-valid-hash") is False


def test_access_token_roundtrip_contains_exp():
    token = security.create_access_token({"sub": "staff-123"})
    payload = security.decode_token(token)
    assert payload["sub"] == "staff-123"
    assert "exp" in payload


def test_refresh_token_is_typed():
    token = security.create_refresh_token({"sub": "staff-123"})
    payload = security.decode_token(token)
    assert payload["type"] == "refresh"


def test_expired_token_is_rejected():
    token = security.create_access_token(
        {"sub": "staff-123"}, expires_delta=timedelta(minutes=-5)
    )
    with pytest.raises(ValueError):
        security.decode_token(token)


def test_garbage_token_is_rejected():
    with pytest.raises(ValueError):
        security.decode_token("garbage.token.value")
