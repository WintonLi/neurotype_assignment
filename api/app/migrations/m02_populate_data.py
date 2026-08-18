from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import secrets
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import insert, select

from app.app_logging import logger
from app.assessment.models import Assessment
from app.auth.models import User
from app.database import engine


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


def _default_data_file() -> Path:
    configured_path = os.getenv("DATA_FILE")
    if configured_path:
        return Path(configured_path)
    return Path(__file__).resolve().parents[3] / "data" / "assessments.jsonl"


def _valid_item(item: Any) -> bool:
    return (
        isinstance(item, dict)
        and isinstance(item.get("code"), str)
        and isinstance(item.get("max"), (int, float))
        and item["max"] > 0
        and isinstance(item.get("completed"), bool)
        and (
            item.get("raw") is None
            or isinstance(item.get("raw"), (int, float))
        )
    )


def _valid_domains(domains: Any) -> bool:
    if not isinstance(domains, list) or not domains:
        return False
    return all(
        isinstance(domain, dict)
        and isinstance(domain.get("domain"), str)
        and isinstance(domain.get("items"), list)
        and bool(domain["items"])
        and all(_valid_item(item) for item in domain["items"])
        for domain in domains
    )


def _assessment_from_record(record: Any, line_number: int) -> Assessment | None:
    if not isinstance(record, dict):
        logger.warning("Skipping line %d: assessment record is not a JSON object", line_number)
        return None

    client = record.get("client")
    domains = record.get("domains")
    required_scalars = ("assessment_id", "assessed_at", "clinician_id", "summary")
    if not all(isinstance(record.get(field), str) and record[field] for field in required_scalars):
        logger.warning("Skipping line %d: missing or invalid assessment fields", line_number)
        return None
    if not isinstance(client, dict):
        logger.warning("Skipping line %d: client is not valid JSON object data", line_number)
        return None
    if not _valid_domains(domains):
        logger.warning("Skipping line %d: domains is not a valid JSON list", line_number)
        return None
    if not all(
        isinstance(client.get(field), str) and client[field]
        for field in ("date_of_birth", "nhs_number", "guardian_contact")
    ):
        logger.warning("Skipping line %d: client contains invalid required fields", line_number)
        return None

    try:
        assessed_at = datetime.fromisoformat(record["assessed_at"])
        date.fromisoformat(client["date_of_birth"])
    except ValueError:
        logger.warning("Skipping line %d: invalid assessment or birth date", line_number)
        return None

    return Assessment(
        id=record["assessment_id"],
        date_of_birth=client["date_of_birth"],
        nhs_number=client["nhs_number"],
        guardian_contact=client["guardian_contact"],
        safeguarding_notes=client.get("safeguarding_notes"),
        assessed_at=assessed_at,
        clinician_username=record["clinician_id"],
        domains=domains,
        summary=record["summary"],
        status="pending_review",
    )


async def migrate(data_file: str | Path | None = None) -> None:
    """Populate assessments from the JSONL source, skipping invalid records."""
    source_path = Path(data_file) if data_file is not None else _default_data_file()
    if not source_path.is_file():
        logger.error("Migration m02_populate_data could not find %s", source_path)
        return

    async with engine.begin() as connection:
        existing_ids = set(
            await connection.run_sync(
                lambda sync_connection: {
                    row[0] for row in sync_connection.execute(select(Assessment.id))
                }
            )
        )

    imported = 0
    skipped = 0
    duplicates = 0
    assessments: list[Assessment] = []
    with source_path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                logger.warning("Skipping line %d: invalid JSON (%s)", line_number, error.msg)
                skipped += 1
                continue

            assessment = _assessment_from_record(record, line_number)
            if assessment is None:
                skipped += 1
                continue
            if assessment.id in existing_ids:
                logger.info("Skipping line %d: assessment %s already exists", line_number, assessment.id)
                duplicates += 1
                continue
            existing_ids.add(assessment.id)
            assessments.append(assessment)

    if assessments:
        async with engine.begin() as connection:
            existing_clinicians = set(
                await connection.run_sync(
                    lambda sync_connection: {
                        row[0]
                        for row in sync_connection.execute(
                            select(User.username).where(
                                User.username.in_(
                                    {assessment.clinician_username for assessment in assessments}
                                )
                            )
                        )
                    }
                )
            )
            missing_clinicians = {
                assessment.clinician_username
                for assessment in assessments
                if assessment.clinician_username not in existing_clinicians
            }
            if missing_clinicians:
                await connection.run_sync(
                    lambda sync_connection: sync_connection.execute(
                        insert(User),
                        [
                            {
                                "username": username,
                                "password_hash": _hash_password("123"),
                                "roles": ["clinician"],
                            }
                            for username in sorted(missing_clinicians)
                        ],
                    )
                )
                logger.info(
                    "Migration m02_populate_data created clinician users: %s",
                    ", ".join(sorted(missing_clinicians)),
                )

            await connection.run_sync(
                lambda sync_connection: sync_connection.execute(
                    insert(Assessment),
                    [
                        {
                            column.name: getattr(assessment, column.name)
                            for column in Assessment.__table__.columns
                            if column.name not in {"issued_at", "issued_by"}
                        }
                        for assessment in assessments
                    ],
                )
            )
        imported = len(assessments)

    logger.info(
        "Migration m02_populate_data finished: imported=%d, invalid=%d, duplicates=%d",
        imported,
        skipped,
        duplicates,
    )


if __name__ == "__main__":
    asyncio.run(migrate())