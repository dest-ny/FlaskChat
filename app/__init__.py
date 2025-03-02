# Archivo de inicialización de la aplicación Flask
from flask import Flask
from flaskext.mysql import MySQL
from flask_socketio import SocketIO
from flask_bcrypt import Bcrypt
from pymysql.cursors import DictCursor

# Creación de la instancia principal de la aplicación Flask
app = Flask(__name__)
app.debug = True

# Configuración de la aplicación
app.config['SECRET_KEY'] = "secret!"  # Clave secreta para sesiones y tokens
# Configuración de la conexión a la base de datos MySQL
app.config['MYSQL_DATABASE_HOST'] = "192.168.1.117"
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_USER'] = "flaskchat"
app.config['MYSQL_DATABASE_PASSWORD'] = "flaskchat"
app.config['MYSQL_DATABASE_DB'] = "flaskchat"

# Inicialización de extensiones
socketio = SocketIO(app)  # Socket.IO para comunicación en tiempo real
mysql = MySQL(app=app, cursorclass=DictCursor)  # Conexión a MySQL con cursor que devuelve diccionarios
flask_bcrypt = Bcrypt(app)  # Herramienta para encriptar contraseñas

# Importación y registro del blueprint principal
from app.chat.controllers import main
app.register_blueprint(main)