"""As migrações criam exatamente o esquema dos modelos."""

from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from copiloto.db.models import Base

ROOT = Path(__file__).resolve().parents[2]


def test_upgrade_creates_all_tables_and_matches_models(tmp_path):
    url = f"sqlite:///{tmp_path / 'mig.db'}"
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    engine = create_engine(url)
    tables = set(inspect(engine).get_table_names()) - {"alembic_version"}
    assert tables == set(Base.metadata.tables)
    with engine.connect() as con:
        diff = compare_metadata(MigrationContext.configure(con), Base.metadata)
    assert diff == []

    command.downgrade(cfg, "base")
    assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
