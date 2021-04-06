from datetime import datetime

from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import set_access_cookies
from flask_jwt_extended import unset_jwt_cookies


from timetable.adapters.orm import start_mappers
from timetable.config import get_database_uri, get_secret_key
from timetable.domain.exceptions import NotAvailableError, DoesNotExistsError

from timetable.domain.command import (
    CreateClient,
    CreateService,
    CreateAppointment,
    AcceptAppointment,
    GetUser,
    GetAppointment,
    ListAppointments,
    SearchServices,
)
from timetable.service_layer.message_bus import MessageBus
from timetable.service_layer.unit_of_work import SqlUnitOfWork

flask_app = Flask(__name__)
jwt = JWTManager(flask_app)
flask_app.config["JWT_SECRET_KEY"] = get_secret_key()
flask_app.config["JWT_TOKEN_LOCATION"] = ["cookies"]


engine = create_engine(get_database_uri())
start_mappers()
session_factory = sessionmaker(bind=engine)

uow = SqlUnitOfWork(session_factory=session_factory)
mb = MessageBus()


@flask_app.route("/service", methods=["GET"])
def get_services():
    tags = request.args.get("tags")
    if tags:
        tags = tags.split(",")
    else:
        tags = []
    c = SearchServices(tags)
    [ss] = mb.handle(c, uow)
    return jsonify(ss), 200


@flask_app.route("/service/<string:account_name>/appointment", methods=["GET"])
@jwt_required(optional=True)
def get_appointments(account_name):
    current_identity = get_jwt_identity()

    c = ListAppointments(account_name, current_identity)
    try:
        [list_dict_app] = mb.handle(c, uow)
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
    current_identity = get_jwt_identity()
    if current_identity == account_name:
        c = GetAppointment(account_name, app_id)
        try:
            [a] = mb.handle(c, uow)
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
    c = CreateAppointment(
        account_name,
        get_jwt_identity(),
        datetime.strptime(j["since"], "%Y-%m-%d %H:%M"),
        datetime.strptime(j["until"], "%Y-%m-%d %H:%M"),
        j["description"],
    )
    try:
        [dict_app] = mb.handle(
            c,
            uow,
        )
    except (DoesNotExistsError, ValueError) as e:
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
    current_user = get_jwt_identity()
    if current_user == account_name:
        c = AcceptAppointment(account_name, app_id)
        try:
            [dict_app] = mb.handle(c, uow)
        except DoesNotExistsError as e:
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
    if account_type == "client":
        c = CreateClient(account_name, email, password)
    elif account_type == "service":
        tags = j["tags"]
        c = CreateService(account_name, email, password, tags)
    try:
        [u] = mb.handle(c, uow)
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
    c = GetUser(account_name)
    try:
        [user] = mb.handle(c, uow)
    except DoesNotExistsError:
        r = {"error": "wrong username or password"}, 400
    else:
        if user["password"] != password:
            r = {"error": "wrong username or password"}, 400
        else:
            access_token = create_access_token(identity=user["account_name"])
            js = jsonify(
                {"msg": "login successful", "account_name": account_name}
            )
            set_access_cookies(js, access_token)
            r = js, 200
    return r


@flask_app.route("/logout", methods=["POST"])
def logout():
    js = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(js)
    return js, 200
