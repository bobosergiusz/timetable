from flask import Blueprint, request

from timetable.domain.command import (
    CreateClient,
    CreateService,
)
from timetable.service_layer.views import get_user
from timetable.domain.exceptions import NotAvailableError, DoesNotExistsError
from timetable.entrypoints.bootstrap import mb, uow

user = Blueprint("user", __name__)


@user.route("/user", methods=["POST"])
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
        mb.handle(c, uow)
    except NotAvailableError as e:
        r = {"error": str(e)}, 400
    else:
        r = {"msg": "ok"}, 201
    return r


@user.route("/user/<string:account_name>", methods=["GET"])
def get_user_detail(account_name):
    try:
        u = get_user(account_name, uow)
    except DoesNotExistsError as e:
        r = {"error": str(e)}, 400
    else:
        del u["password"]
        r = u, 200
    return r
