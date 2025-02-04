from flask import Flask
from flaskext.mysql import MySQL
from flask_socketio import SocketIO

app = Flask(__name__)
app.debug = True

app.config['SECRET_KEY'] = "secret!"
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_PORT'] = "8003"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = ""
app.config['MYSQL_DB'] = "flaskchat"

socketio = SocketIO(app)
mysql = MySQL(app)

from app.chat.controllers import main
app.register_blueprint(main)