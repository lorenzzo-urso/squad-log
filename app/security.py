import hashlib
import hmac
import secrets

_ITERATIONS = 200_000


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITERATIONS)
    return digest.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    candidate, _ = hash_password(password, salt)
    return hmac.compare_digest(candidate, password_hash)


def generate_api_token() -> str:
    return f"sqlg_{secrets.token_urlsafe(32)}"


def hash_api_token(token: str) -> str:
    # Tokens are high-entropy random strings (unlike passwords), so a plain
    # fast hash is the norm here (checked on every API call, not just login).
    return hashlib.sha256(token.encode()).hexdigest()
