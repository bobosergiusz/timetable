from datetime import datetime

from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity


from timetable.adapters.orm import start_mappers
from timetable.config import get_database_uri, get_secret_key
from timetable.domain.exceptions import NotAvailableError, DoesNotExistsError

from timetable.service_layer.services import (
    accept_appointment,
    create_appointment,
    list_appointments_owned,
    list_appointments_unowned,
    create_client,
    create_service,
    search_services,
    get_user,
    get_appointment,
)
from timetable.service_layer.unit_of_work import SqlUnitOfWork

flask_app = Flask(__name__)
jwt = JWTManager(flask_app)
flask_app.config["JWT_SECRET_KEY"] = get_secret_key()


engine = create_engine(get_database_uri())
start_mappers()
session_factory = sessionmaker(bind=engine)


@flask_app.route("/service", methods=["GET"])
def get_services():
    tags = request.args.get("tags")
    if tags:
        tags = tags.split(",")
    else:
        tags = []
    uow = SqlUnitOfWork(session_factory=session_factory)
    ss = search_services(tags, uow)
    return jsonify(ss), 200


@flask_app.route("/service/<string:account_name>/appointment", methods=["GET"])
@jwt_required(optional=True)
def get_appointments(account_name):
    uow = SqlUnitOfWork(session_factory=session_factory)
    current_identity = get_jwt_identity()
    if current_identity == account_name:
        fun = list_appointments_owned
    else:
        fun = list_appointments_unowned
    try:
        list_dict_app = fun(account_name, uow)
    except DoesNotExistsError as e:
        r = {"error": str(e)}, 400
    else:
        for dict_app in list_dict_app:
            dict_app["since"] = dict_app["since"].strftime("%Y-%m-%d %H:%M")
            dict_app["until"] = dict_app["until"].strftime("%Y-%m-%d %H:%M")
        r = jsonify(list_dict_app), 200
    return r


@flask_app.route(
    "/service/<string:account_name>/appointment/<int:app_id>", methods=["GET"]
)
@jwt_required()
def get_appointment_detail(account_name, app_id):
    uow = SqlUnitOfWork(session_factory=session_factory)
    current_identity = get_jwt_identity()
    if current_identity == account_name:
        try:
            a = get_appointment(account_name, app_id, uow)
        except DoesNotExistsError as e:
            r = {"error": str(e)}, 400
        else:
            a["since"] = a["since"].strftime("%Y-%m-%d %H:%M")
            a["until"] = a["until"].strftime("%Y-%m-%d %H:%M")
            r = a, 200
    else:
        r = {"error": "unauthorized"}, 401
    return r


@flask_app.route(
    "/service/<string:account_name>/appointment", methods=["POST"]
)
@jwt_required()
def post_appointment(account_name):
    j = request.json
    from_user = get_jwt_identity()
    since = datetime.strptime(j["since"], "%Y-%m-%d %H:%M")
    until = datetime.strptime(j["until"], "%Y-%m-%d %H:%M")
    description = j["description"]
    uow = SqlUnitOfWork(session_factory=session_factory)
    try:
        dict_app = create_appointment(
            to_user=account_name,
            from_user=from_user,
            since=since,
            until=until,
            description=description,
            uow=uow,
        )
    except (DoesNotExistsError, NotAvailableError, ValueError) as e:
        j = {"error": str(e)}
        status_code = 400
    else:
        dict_app["since"] = dict_app["since"].strftime("%Y-%m-%d %H:%M")
        dict_app["until"] = dict_app["until"].strftime("%Y-%m-%d %H:%M")
        j = dict_app
        status_code = 201
    return j, status_code


@flask_app.route(
    "/service/<string:account_name>/appointment/<int:app_id>", methods=["PUT"]
)
@jwt_required()
def put_appointment(account_name, app_id):
    uow = SqlUnitOfWork(session_factory=session_factory)
    current_user = get_jwt_identity()
    if current_user == account_name:
        try:
            dict_app = accept_appointment(account_name, app_id, uow)
        except (DoesNotExistsError, NotAvailableError) as e:
            j = {"error": str(e)}
            status_code = 400
        else:
            dict_app["since"] = dict_app["since"].strftime("%Y-%m-%d %H:%M")
            dict_app["until"] = dict_app["until"].strftime("%Y-%m-%d %H:%M")
            j = dict_app
            status_code = 200
    else:
        j = {"error": "unauthorized"}
        status_code = 401
    return j, status_code


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
            r = {"error": str(e)}, 400
        else:
            r = u, 201
    elif account_type == "service":
        tags = j["tags"]
        try:
            u = create_service(account_name, email, password, tags, uow)
        except NotAvailableError as e:
            r = {"error": str(e)}, 400
        else:
            r = u, 201
    return r


jwt = JWTManager(flask_app)


@flask_app.route("/login", methods=["POST"])
def login():
    j = request.json
    account_name = j["account_name"]
    password = j["password"]
    uow = SqlUnitOfWork(session_factory=session_factory)

    try:
        user = get_user(account_name, uow)
    except DoesNotExistsError:
        r = {"error": "wrong username or password"}, 400
    else:
        if user["password"] != password:
            r = {"error": "wrong username or password"}, 400
        else:
            access_token = create_access_token(identity=user["account_name"])
            r = {"access_token": access_token}, 200
    return r
