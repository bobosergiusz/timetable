from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from flask_jwt_extended import set_access_cookies
from flask_jwt_extended import unset_jwt_cookies

from timetable.service_layer.views import get_user
from timetable.domain.exceptions import DoesNotExistsError
from timetable.entrypoints.deps import mb

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["POST"])
def login():
    j = request.json
    account_name = j["account_name"]
    password = j["password"]
    try:
        user = get_user(account_name, mb.uow)
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


@auth.route("/logout", methods=["POST"])
def logout():
    js = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(js)
    return js, 200
