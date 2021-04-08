from flask import Flask

from flask_jwt_extended import JWTManager


from timetable.config import get_secret_key
from timetable.entrypoints.auth import auth
from timetable.entrypoints.service import service
from timetable.entrypoints.user import user

flask_app = Flask(__name__)
flask_app.config["JWT_SECRET_KEY"] = get_secret_key()
flask_app.config["JWT_TOKEN_LOCATION"] = ["cookies"]

flask_app.register_blueprint(auth)
flask_app.register_blueprint(service)
flask_app.register_blueprint(user)

jwt = JWTManager(flask_app)
