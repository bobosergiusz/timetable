from flask_jwt_extended import JWTManager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from timetable.config import get_database_uri
from timetable.service_layer.unit_of_work import SqlUnitOfWork
from timetable.bootstrap import bootstrap

jwt = JWTManager()

engine = create_engine(get_database_uri())
session_factory = sessionmaker(bind=engine)
uow = SqlUnitOfWork(session_factory=session_factory)

mb = bootstrap(True, uow)
