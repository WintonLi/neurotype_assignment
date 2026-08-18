import asyncio

from sqlalchemy import inspect

from app.app_logging import logger
from app.assessment import models as assessment_models
from app.audit import models as audit_models
from app.auth import models as auth_models
from app.database import Base, engine


async def migrate() -> None:
	"""Create the application's auth, assessment, and audit tables."""
	# Importing the model modules registers all tables and relationships with Base.metadata.
	_ = (auth_models, assessment_models, audit_models)
	required_tables = {
		auth_models.User.__tablename__,
		assessment_models.Assessment.__tablename__,
		audit_models.AuditEvent.__tablename__,
	}

	async with engine.begin() as connection:
		existing_tables = set(
			await connection.run_sync(
				lambda sync_connection: inspect(sync_connection).get_table_names()
			)
		)
		missing_tables = required_tables - existing_tables

		if not missing_tables:
			logger.info(
				"Migration m01_create_tables skipped; tables already exist: %s",
				", ".join(sorted(required_tables)),
			)
			return

		await connection.run_sync(
			lambda sync_connection: Base.metadata.create_all(
				sync_connection,
				tables=[
					table
					for table in Base.metadata.sorted_tables
					if table.name in missing_tables
				],
				checkfirst=True,
			)
		)
		logger.info(
			"Migration m01_create_tables created tables: %s",
			", ".join(sorted(missing_tables)),
		)

if __name__ == "__main__":
    asyncio.run(migrate())
