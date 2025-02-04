from flask import Flask, Blueprint
from flask_socketio import SocketIO

app = Flask(__name__)
app.debug = True

app.config['SECRET_KEY'] = "secret!"

socketio = SocketIO(app)

from app.chat.controllers import main
app.register_blueprint(main)