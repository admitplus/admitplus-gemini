import bcrypt
import secrets
import string
import uuid


def generate_secure_token(length: int = 32, use_urlsafe: bool = True) -> str:
    """
    Generate a secure random token.

    Args:
        length: Length of the token (default: 32)
        use_urlsafe: If True, use URL-safe base64 encoding. If False, use alphanumeric characters.

    Returns:
        A secure random token string
    """
    if use_urlsafe:
        return secrets.token_urlsafe(length)
    else:
        return "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(length)
        )


def generate_refresh_token() -> str:
    """
    Generate a refresh token using URL-safe base64 encoding.
    This is the recommended method for refresh tokens.
    """
    return generate_secure_token(32, use_urlsafe=True)


def generate_invite_token() -> str:
    """
    Generate an invite token using alphanumeric characters.
    This is suitable for invite codes that might be manually entered.
    """
    return generate_secure_token(8, use_urlsafe=False)


def generate_uuid() -> str:
    """
    Generate a UUID4 string for use as a unique identifier.
    This is the standard method for generating unique IDs in the system.
    """
    try:
        return str(uuid.uuid4())
    except Exception as e:
        raise Exception(f"Failed to generate UUID: {e}")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(stored_hash: str, input_password: str) -> bool:
    """Verify a password against the stored hash."""
    return bcrypt.checkpw(input_password.encode("utf-8"), stored_hash.encode("utf-8"))
