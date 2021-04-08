from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from timetable.adapters.orm import start_mappers
from timetable.config import get_database_uri
from timetable.service_layer.message_bus import MessageBus
from timetable.service_layer.unit_of_work import SqlUnitOfWork


engine = create_engine(get_database_uri())
start_mappers()
session_factory = sessionmaker(bind=engine)

uow = SqlUnitOfWork(session_factory=session_factory)
mb = MessageBus()
