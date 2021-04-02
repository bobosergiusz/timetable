from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    MetaData,
    Table,
)
from sqlalchemy.ext.associationproxy import association_proxy

from sqlalchemy.orm import mapper, relationship

from timetable.domain.appointment import Appointment
from timetable.domain.user import User, Client, Service
from timetable.domain.calendar import Calendar

metadata = MetaData()

calendars = Table(
    "calendars",
    metadata,
    Column("owner", ForeignKey("services.account_name"), primary_key=True),
    Column("id_count", Integer),
)

appointments = Table(
    "appointments",
    metadata,
    Column("calendar_owner", ForeignKey("calendars.owner"), primary_key=True),
    Column("id", Integer, primary_key=True),
    Column("from_user", String, nullable=False),
    Column("until", DateTime, nullable=False),
    Column("since", DateTime, nullable=False),
    Column("description", String, nullable=False),
    Column("accepted", Boolean, nullable=False),
)


users = Table(
    "users",
    metadata,
    Column("account_name", String(30), primary_key=True),
    Column("email", String(30), nullable=False),
    Column("password", String(30), nullable=False),
    Column("type", String(30)),
)

clients = Table(
    "clients",
    metadata,
    Column(
        "account_name",
        String(30),
        ForeignKey("users.account_name"),
        primary_key=True,
    ),
)

services = Table(
    "services",
    metadata,
    Column(
        "account_name",
        String(30),
        ForeignKey("users.account_name"),
        primary_key=True,
    ),
)


class Tag:
    def __init__(self, tag):
        self.tag = tag


tags = Table(
    "tags",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("service_account_name", ForeignKey("services.account_name")),
    Column("tag", String(30)),
)


def start_mappers():

    mapper(
        Calendar,
        calendars,
        properties={
            "_appointments": relationship(
                Appointment, cascade="all, delete-orphan"
            ),
        },
    )
    mapper(Appointment, appointments)
    mapper(
        User, users, polymorphic_on=users.c.type, polymorphic_identity="user"
    )
    mapper(Client, clients, inherits=User, polymorphic_identity="client")
    mapper(
        Tag,
        tags,
    )
    mapper(
        Service,
        services,
        inherits=User,
        polymorphic_identity="service",
        properties={"_tg": relationship(Tag)},
    )
    Service.tags = association_proxy("_tg", "tag")
