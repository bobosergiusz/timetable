from datetime import datetime

from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token
from flask_jwt_extended import current_user


from timetable.adapters.orm import start_mappers
from timetable.adapters.repository import DoesNotExistsError
from timetable.config import get_database_uri, get_secret_key
from timetable.domain.accept import NotAvailableError
from timetable.service_layer.services import (
    accept_appointment,
    ask_appointment,
    list_appointments,
    create_client,
    create_service,
    get_user,
)
from timetable.service_layer.unit_of_work import SqlUnitOfWork

flask_app = Flask(__name__)
jwt = JWTManager(flask_app)
flask_app.config["JWT_SECRET_KEY"] = get_secret_key()


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


@flask_app.route("/user", methods=["POST"])
def create_user():
    j = request.json
    account_name = j["account_name"]
    email = j["email"]
    password = j["password"]
    # TODO: hash password
    account_type = j["account_type"]
    uow = SqlUnitOfWork(session_factory=session_factory)
    if account_type == "client":
        try:
            u = create_client(account_name, email, password, uow)
        except NotAvailableError as e:
            r = {"msg": str(e)}, 400
        else:
            r = u, 201
    elif account_type == "service":
        tags = j["tags"]
        try:
            u = create_service(account_name, email, password, tags, uow)
        except NotAvailableError as e:
            r = {"msg": str(e)}, 400
        else:
            r = u, 201
    return r


jwt = JWTManager(flask_app)


@jwt.user_identity_loader
def user_identity_lookup(user: dict):
    return user["account_name"]


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    account_name = jwt_data["sub"]
    uow = SqlUnitOfWork(session_factory=session_factory)
    try:
        u = get_user(account_name, uow)
    except DoesNotExistsError:
        u = None
    return u


# TODO: add this two routes with JWT
# TODO: write e2e test for creating a user, login and accessing second endpoint
@flask_app.route("/login", methods=["POST"])
def login():
    j = request.json
    account_name = j["account_name"]
    password = j["password"]
    uow = SqlUnitOfWork(session_factory=session_factory)

    try:
        user = get_user(account_name, uow)
    except DoesNotExistsError:
        r = {"msg": "wrong username or password"}, 400
    else:
        if user["password"] != password:
            r = {"msg": "wrong username or password"}, 400
        else:
            access_token = create_access_token(identity=user)
            r = {"access_token": access_token}, 200
    return r


@flask_app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    msg = f"You are user: {current_user['account_name']}"
    return {"msg": msg}, 200
