# Inicialización del módulo de controladores
from flask import Blueprint

# Creación del Blueprint principal para organizar las rutas de la aplicación
main = Blueprint('main', __name__)

# Importación de los módulos de rutas y eventos para registrarlos en el Blueprint
from . import routes, events