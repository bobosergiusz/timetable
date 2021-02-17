from datetime import datetime

from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from timetable.adapters.orm import start_mappers
from timetable.adapters.repository import DoesNotExistsError
from timetable.config import get_database_uri
from timetable.domain.accept import NotAvailableError
from timetable.service_layer.services import (
    accept_appointment,
    ask_appointment,
    list_appointments,
)
from timetable.service_layer.unit_of_work import SqlUnitOfWork

flask_app = Flask(__name__)

engine = create_engine(get_database_uri())
start_mappers()
session_factory = sessionmaker(bind=engine)


@flask_app.route("/appointment", methods=["POST"])
def post_appointment():
    j = request.json
    since = datetime.strptime(j["since"], "%Y-%m-%d %H:%M")
    until = datetime.strptime(j["until"], "%Y-%m-%d %H:%M")
    uow = SqlUnitOfWork(session_factory=session_factory)
    try:
        dict_app = ask_appointment(since=since, until=until, uow=uow)
    except (DoesNotExistsError, NotAvailableError) as e:
        j = {"msg": str(e)}
        status_code = 400
    else:
        dict_app["since"] = dict_app["since"].strftime("%Y-%m-%d %H:%M")
        dict_app["until"] = dict_app["until"].strftime("%Y-%m-%d %H:%M")
        j = dict_app
        status_code = 201
    return j, status_code


@flask_app.route("/appointment/<int:id>", methods=["PUT"])
def put_appointment(id):
    uow = SqlUnitOfWork(session_factory=session_factory)
    try:
        dict_app = accept_appointment(id, uow)
    except (DoesNotExistsError, NotAvailableError) as e:
        j = {"msg": str(e)}
        status_code = 400
    else:
        dict_app["since"] = dict_app["since"].strftime("%Y-%m-%d %H:%M")
        dict_app["until"] = dict_app["until"].strftime("%Y-%m-%d %H:%M")
        j = dict_app
        status_code = 200
    return j, status_code


@flask_app.route("/appointment", methods=["GET"])
def get_appointment():
    uow = SqlUnitOfWork(session_factory=session_factory)
    list_dict_app = list_appointments(uow)
    for dict_app in list_dict_app:
        dict_app["since"] = dict_app["since"].strftime("%Y-%m-%d %H:%M")
        dict_app["until"] = dict_app["until"].strftime("%Y-%m-%d %H:%M")
    return jsonify(list_dict_app), 200
