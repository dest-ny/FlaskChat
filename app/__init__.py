from flask import Flask
from flaskext.mysql import MySQL
from flask_socketio import SocketIO
from flask_bcrypt import Bcrypt
from pymysql.cursors import DictCursor

app = Flask(__name__)
app.debug = True

app.config['SECRET_KEY'] = "secret!"
app.config['MYSQL_DATABASE_HOST'] = "192.168.1.117"
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_USER'] = "flaskchat"
app.config['MYSQL_DATABASE_PASSWORD'] = "flaskchat"
app.config['MYSQL_DATABASE_DB'] = "flaskchat"

socketio = SocketIO(app)
mysql = MySQL(app=app, cursorclass=DictCursor)
flask_bcrypt = Bcrypt(app)
from app.chat.controllers import main
app.register_blueprint(main)