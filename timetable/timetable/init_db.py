from sqlalchemy import create_engine

from timetable.adapters.orm import metadata
from timetable.config import get_database_uri


def init_db():
    engine = create_engine(get_database_uri())
    metadata.create_all(engine)
