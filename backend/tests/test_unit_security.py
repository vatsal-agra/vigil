"""Unit tests for password hashing and tokens (app/security.py)."""
import jwt
import pytest

from app.config import settings
from app.security import create_token, hash_password, verify_password

pytestmark = pytest.mark.unit


def test_password_round_trip():
    stored = hash_password("vigil-demo-2026")
    assert verify_password("vigil-demo-2026", stored)
    assert not verify_password("wrong-password", stored)


def test_hashes_are_salted_pbkdf2():
    a, b = hash_password("same-password"), hash_password("same-password")
    assert a != b
    assert a.startswith("pbkdf2_sha256$120000$")


def test_a_malformed_stored_hash_is_rejected_not_raised():
    assert verify_password("anything", "not-a-hash") is False


def test_token_carries_the_user_id_and_an_expiry():
    payload = jwt.decode(create_token(42), settings.jwt_secret, algorithms=["HS256"])
    assert payload["sub"] == "42"
    assert "exp" in payload
