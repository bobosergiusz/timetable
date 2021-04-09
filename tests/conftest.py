from pytest import fixture
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers

from timetable.adapters.orm import metadata, start_mappers
from timetable.domain.user import Service
from timetable.service_layer.unit_of_work import SqlUnitOfWork
from timetable.bootstrap import bootstrap

from tests.fakes import FakeUnitOfWork


@fixture
def Session():
    engine = create_engine("sqlite://")
    Session = sessionmaker(bind=engine)
    metadata.create_all(engine)
    start_mappers()
    yield Session
    clear_mappers()
    del Service.tags


@fixture
def fake_mb():
    return bootstrap(False, FakeUnitOfWork())
