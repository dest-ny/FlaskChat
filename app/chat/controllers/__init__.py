from flask import Blueprint

main = Blueprint('main', __name__)
USUARIOS = []

from . import routes, events