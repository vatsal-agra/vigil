from app.security import hash_password, verify_password
from app.services import slugify


def test_password_round_trip():
    stored = hash_password("vigil-demo-2026")
    assert verify_password("vigil-demo-2026", stored)
    assert not verify_password("wrong-password", stored)


def test_slugify_handles_punctuation():
    assert slugify("Checkout API (v2)!") == "checkout-api-v2"
    assert slugify("!!!") == "monitor"
