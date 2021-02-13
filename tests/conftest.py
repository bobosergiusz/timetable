from pytest import fixture
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from timetable.adapters.orm import metadata, start_mappers


@fixture
def Session():
    engine = create_engine("sqlite://")
    Session = sessionmaker(bind=engine)
    metadata.create_all(engine)
    start_mappers()
    return Session
