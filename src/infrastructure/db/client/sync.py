"""
Sync database client.
"""

from contextlib import contextmanager

import sqlalchemy as sa
import sqlalchemy.orm as orm

from infrastructure.db.utils.types import SessionGenerator


class Database:
    def __init__(self, db_url: str, echo: bool = False) -> None:
        self._engine = sa.create_engine(db_url, echo=echo)
        self._session_factory = orm.scoped_session(
            orm.sessionmaker(
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
                bind=self._engine,
            ),
        )

    @contextmanager
    def session(self) -> SessionGenerator:
        session: orm.Session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
