"""Tests for password hashing functions (app.core.security)."""

import re

from app.core.security import hash_password, verify_password


def test_hash_password_returns_bcrypt_format():
    """Hash starts with $2b$ bcrypt prefix."""
    hashed = hash_password("testpass123")
    assert hashed.startswith("$2b$")
    assert len(hashed) == 60  # standard bcrypt hash length


def test_hash_password_returns_string():
    """Hash is a string (not bytes)."""
    hashed = hash_password("anypass")
    assert isinstance(hashed, str)


def test_verify_password_correct():
    """Correct password returns True."""
    hashed = hash_password("mysecret")
    assert verify_password("mysecret", hashed) is True


def test_verify_password_incorrect():
    """Wrong password returns False."""
    hashed = hash_password("mysecret")
    assert verify_password("wrongpass", hashed) is False


def test_verify_password_empty_wrong():
    """Empty string as wrong password returns False."""
    hashed = hash_password("somepass")
    assert verify_password("", hashed) is False


def test_hash_and_verify_roundtrip():
    """Hash then verify with same password succeeds."""
    passwords = ["pass1", "abc123", "P@ssw0rd!", "1234567890"]
    for pwd in passwords:
        hashed = hash_password(pwd)
        assert verify_password(pwd, hashed) is True
        assert verify_password(pwd + "x", hashed) is False


def test_hash_unique_per_call():
    """Same password produces different hashes (different salt)."""
    pwd = "consistent"
    h1 = hash_password(pwd)
    h2 = hash_password(pwd)
    assert h1 != h2
    # Both should still verify correctly
    assert verify_password(pwd, h1) is True
    assert verify_password(pwd, h2) is True


def test_hash_contains_only_expected_chars():
    """Bcrypt hash contains only valid base64 characters."""
    hashed = hash_password("any")
    # $2b$rounds$salt+hash (all base64: a-z, A-Z, 0-9, /, .)
    assert re.fullmatch(r"\$2b\$[0-9]{2}\$[A-Za-z0-9/\.]{53}", hashed)


def test_verify_bcrypt_format_hash():
    """Verify a hash produced directly by bcrypt library (same format passlib used).

    passlib uses the same underlying bcrypt algorithm, so any standard
    $2b$ hash is verifiable regardless of which library produced it.
    """
    import bcrypt as _bcrypt
    pwd = b"cross_library_test"
    known_hash = _bcrypt.hashpw(pwd, _bcrypt.gensalt()).decode()
    assert verify_password(pwd.decode(), known_hash) is True


def test_verify_unicode_password():
    """Unicode passwords work correctly."""
    passwords = [
        "héllo",          # accented
        "密码",            # CJK
        "パスワード",       # Japanese
        "😊🔐",           # emoji
        "a\u0000b",       # null byte (valid in bcrypt)
    ]
    for pwd in passwords:
        hashed = hash_password(pwd)
        assert verify_password(pwd, hashed) is True


def test_verify_long_password():
    """Bcrypt supports up to 72 bytes; longer passwords are truncated."""
    pwd = "a" * 100  # longer than 72 bytes
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed) is True
    # bcrypt truncates at 72 bytes, so first 72 chars = same hash
    assert verify_password("a" * 72, hashed) is True
