from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./contracts.db")

# Normalize Render Postgres URLs (postgres:// -> postgresql+psycopg2://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
	DATABASE_URL,
	connect_args=connect_args,
	future=True,
)

SessionLocal = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True))

Base = declarative_base()


def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


def init_db() -> None:
	from . import models  # noqa: F401
	Base.metadata.create_all(bind=engine)
	# Ensure new columns/tables exist for SQLite deployments without migrations
	try:
		with engine.begin() as conn:
			# contracts.production
			res = conn.exec_driver_sql("PRAGMA table_info(contracts)").fetchall()
			cols = {row[1] for row in res}
			if 'production' not in cols:
				conn.exec_driver_sql("ALTER TABLE contracts ADD COLUMN production VARCHAR(255)")
			if 'user_id' not in cols:
				conn.exec_driver_sql("ALTER TABLE contracts ADD COLUMN user_id INTEGER")
	except Exception:
		# Best-effort column addition; ignore if not applicable
		pass 