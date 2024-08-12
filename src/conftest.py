import contextlib
import os
import typing
from collections.abc import Iterable
from pathlib import Path

import pytest
import sqlalchemy as sa
import structlog
from alembic.command import upgrade
from alembic.config import Config
from sqlalchemy import orm
from sqlalchemy_utils import create_database
from sqlalchemy_utils import database_exists
from sqlalchemy_utils import drop_database
from structlog.testing import LogCapture

from infrastructure.db.base import Model
from infrastructure.db.config import DatabaseSettings
from infrastructure.db.types import ModelType
from infrastructure.db.utils.types import SessionFactory
from infrastructure.db.utils.types import SessionGenerator
from infrastructure.tests.types import DBFactoryType
from infrastructure.tests.types import DBInstanceType
from utils.factory import FactoryMakerType


@pytest.fixture(name="log_output")
def fixture_log_output() -> LogCapture:
    return LogCapture()


@pytest.fixture(autouse=True)
def _fixture_configure_structlog(log_output: LogCapture) -> None:
    structlog.configure(processors=[log_output])


def _upgrade_head(url: str, rootdir: str) -> None:
    """
    Upgrade the test database to head.

    :param url: Database URL
    :param rootdir: Root project directory
    """
    config = Config()
    alembic_folder = Path(rootdir) / "src" / "infrastructure" / "db" / "migrations"
    config.set_main_option("script_location", str(alembic_folder))
    config.set_main_option("utils.url", url)

    # heads means all migrations from all branches (in case there are split branches)
    upgrade(config, "heads")


@pytest.fixture(scope="session")
def db_engine(request, worker_id: str) -> typing.Generator[sa.Engine, None, None]:
    os.environ["DB_NAME"] = f"test_{worker_id or 'master'}"  # override default database
    settings = DatabaseSettings()

    if not database_exists(settings.url):
        create_database(settings.url)

    engine = sa.create_engine(settings.url)

    _upgrade_head(settings.url, request.config.rootdir)

    try:
        yield engine
    finally:
        drop_database(settings.url)


@pytest.fixture()
def alembic_engine(db_engine: sa.Engine) -> sa.Engine:
    """
    Override "alembic_engine" fixture of "pytest-alembic" package.

    Check: https://pytest-alembic.readthedocs.io/en/latest/api.html#pytest_alembic.plugin.fixtures.alembic_engine

    :param db_engine: SQLAlchemy Engine instance
    :return: SQLAlchemy Engine instance
    """
    return db_engine


@pytest.fixture()#TODO async
def db_session(db_engine: sa.Engine) -> SessionGenerator:
    connection = db_engine.connect()
    transaction = connection.begin()
    test_local_session = orm.sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection,
        class_=orm.Session,
    )
    session = test_local_session()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()  # rollback to the savepoint
        connection.close()


@pytest.fixture()
def db_session_maker(db_session: orm.Session) -> SessionFactory:
    def session_maker() -> SessionGenerator:
        yield db_session

    return contextlib.contextmanager(session_maker)


@pytest.fixture()
def instance(db_session: orm.Session) -> DBInstanceType:
    """
    SQLAlchemy model instance factory.

    :param db_session: SQLAlchemy session
    :return: Model instance
    """

    def make(*args: Model) -> tuple[Model, ...]:
        try:
            db_session.add_all(args)
            db_session.commit()
        except sa.exc.IntegrityError:
            raise
            # db_session.refresh(args)

        return args

    return make


@pytest.fixture()
def db_factory(instance: DBInstanceType) -> DBFactoryType:
    """
    Uses FactoryMaker for creating database instances.
    """

    def make(factory_maker: FactoryMakerType | None) -> ModelType | tuple[ModelType, ...] | None:
        if factory_maker is None:
            return None

        data: ModelType | Iterable[ModelType] = factory_maker.make()
        if isinstance(data, Iterable):
            return instance(*data)
        else:
            # return only one element
            obj = instance(data)
            return obj[0]

    return make
