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

metadata = MetaData()


appointments = Table(
    "appointments",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("until", DateTime, nullable=False),
    Column("since", DateTime, nullable=False),
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
    _ = mapper(Appointment, appointments)
    _ = mapper(
        User, users, polymorphic_on=users.c.type, polymorphic_identity="user"
    )
    _ = mapper(Client, clients, inherits=User, polymorphic_identity="client")
    _ = mapper(
        Tag,
        tags,
    )
    _ = mapper(
        Service,
        services,
        inherits=User,
        polymorphic_identity="service",
        properties={"_tg": relationship(Tag)},
    )
    Service.tags = association_proxy("_tg", "tag")
