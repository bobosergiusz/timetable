from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity

from timetable.domain.command import (
    CreateAppointment,
    AcceptAppointment,
)
from timetable.service_layer.views import (
    search_services,
    list_appointments,
    get_appointment,
)

from timetable.domain.exceptions import DoesNotExistsError
from timetable.entrypoints.deps import mb


service = Blueprint("service", __name__)


@service.route("/service", methods=["GET"])
def get_services():
    tags = request.args.get("tags")
    if tags:
        tags = tags.split(",")
    else:
        tags = []
    ss = search_services(tags, mb.uow)
    return jsonify(ss), 200


@service.route("/service/<string:account_name>/appointment", methods=["GET"])
@jwt_required(optional=True)
def get_appointments(account_name):
    current_identity = get_jwt_identity()

    try:
        list_dict_app = list_appointments(
            account_name, current_identity, mb.uow
        )
    except DoesNotExistsError as e:
        r = {"error": str(e)}, 400
    else:
        for dict_app in list_dict_app:
            dict_app["since"] = dict_app["since"].strftime("%Y-%m-%d %H:%M")
            dict_app["until"] = dict_app["until"].strftime("%Y-%m-%d %H:%M")
        r = jsonify(list_dict_app), 200
    return r


@service.route(
    "/service/<string:account_name>/appointment/<int:app_id>", methods=["GET"]
)
@jwt_required()
def get_appointment_detail(account_name, app_id):
    current_identity = get_jwt_identity()
    if current_identity == account_name:
        try:
            dict_app = get_appointment(account_name, app_id, mb.uow)
        except DoesNotExistsError as e:
            r = {"error": str(e)}, 400
        else:
            dict_app["since"] = dict_app["since"].strftime("%Y-%m-%d %H:%M")
            dict_app["until"] = dict_app["until"].strftime("%Y-%m-%d %H:%M")
            r = dict_app, 200
    else:
        r = {"error": "unauthorized"}, 401
    return r


@service.route("/service/<string:account_name>/appointment", methods=["POST"])
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
        mb.handle(c)
    except (DoesNotExistsError, ValueError) as e:
        r = {"error": str(e)}, 400
    else:
        r = {"msg": "ok"}, 201
    return r


@service.route(
    "/service/<string:account_name>/appointment/<int:app_id>", methods=["PUT"]
)
@jwt_required()
def put_appointment(account_name, app_id):
    current_user = get_jwt_identity()
    if current_user == account_name:
        c = AcceptAppointment(account_name, app_id)
        try:
            mb.handle(c)
        except DoesNotExistsError as e:
            r = {"error": str(e)}, 400
        else:
            r = {"msg": "ok"}, 200
    else:
        r = {"error": "unauthorized"}, 401
    return r
