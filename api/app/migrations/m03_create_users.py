from __future__ import annotations

import asyncio
import base64
import hashlib
import secrets

from sqlalchemy import insert, select, update

from app.app_logging import logger
from app.assessment import models as assessment_models
from app.auth.models import User
from app.database import engine

USERS = {
    "test": "clinician",
    "reviewer": "reviewer",
}


def _hash_password(password: str) -> str:
    """Return a salted, versioned PBKDF2-SHA256 password hash."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000,
    )
    return "pbkdf2_sha256$600000${}${}".format(
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


async def migrate() -> None:
    """Create or replace the two development users."""
    _ = assessment_models
    async with engine.begin() as connection:
        result = await connection.execute(
            select(User.username).where(User.username.in_(USERS))
        )
        existing_usernames = set(result.scalars())

        created = []
        updated = []
        for username, role in USERS.items():
            password_hash = _hash_password("123")
            if username not in existing_usernames:
                await connection.execute(
                    insert(User).values(
                        username=username,
                        password_hash=password_hash,
                        roles=[role],
                    )
                )
                created.append(username)
            else:
                await connection.execute(
                    update(User)
                    .where(User.username == username)
                    .values(password_hash=password_hash, roles=[role])
                )
                updated.append(username)

    logger.info(
        "Migration m03_create_users finished: created=%s, updated=%s",
        ", ".join(created) or "none",
        ", ".join(updated) or "none",
    )


if __name__ == "__main__":
    asyncio.run(migrate())
