from sqlalchemy import Boolean, Column, DateTime, Integer, MetaData, Table

from sqlalchemy.orm import mapper

from timetable.domain.appointment import Appointment

metadata = MetaData()


appointments = Table(
    "appointments",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("until", DateTime, nullable=False),
    Column("since", DateTime, nullable=False),
    Column("accepted", Boolean, nullable=False),
)


def start_mappers():
    _ = mapper(Appointment, appointments)
