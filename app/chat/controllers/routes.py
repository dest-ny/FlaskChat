# Controlador principal de rutas para la aplicación
from typing import Union

from werkzeug import Response

from app import app
from flask import render_template, session, url_for, request, redirect, flash, jsonify
from app.chat.models.db import *
from datetime import datetime
import psutil
import logging

logger = logging.getLogger(__name__)

def userBanned(name: str) -> bool:
    """
    Verifica si un usuario está actualmente baneado.
    
    Args:
        name (str): Nombre del usuario a verificar
        
    Returns:
        bool: True si el usuario está baneado, False en caso contrario
    """
    try:
        usuario = get_usuario(name=name)
        if usuario:
            if usuario['banned_until'] and datetime.now() < usuario['banned_until']:
                return True
        return False
    except Exception as e:
        logger.error(f"Error checking if user {name} is banned: {e}", exc_info=True)
        return False

@app.route("/")
def chat() -> Union[Response, str]:
    """
    Ruta principal que muestra la interfaz de chat.
    Redirige al login si el usuario no ha iniciado sesión o está baneado.

    Returns:
        Union[Response, str]:
        - Una plantilla HTML (`index.html`) si el usuario ha iniciado sesión y no está baneado.
        - Una redirección (`Response`) a la página de login en caso de que el usuario esté baneado, no haya iniciado sesión u ocurra un error.
    """
    try:
        if 'nombre' in session:
            if userBanned(session['nombre']):
                session.clear()
                flash("HAS SIDO EXPULSADO DEL CHAT", 'error')
                return redirect(url_for('login'))
            return render_template('index.html')
        else:
            return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Error in chat route: {e}", exc_info=True)
        flash("Ha ocurrido un error. Inténtalo de nuevo más tarde.", 'error')
        return redirect(url_for('login'))

@app.route("/load_messages", methods=["GET"])
def load_messages() -> Union[tuple[dict[str, str], int], list, tuple[dict[str, str], int]]:
    """
    Endpoint para cargar mensajes del chat con paginación.
    Requiere que el usuario esté autenticado y no baneado.
    
    Query params:
        offset (int): Número de mensajes a saltar para la paginación.

    Returns:
    - Si el usuario no está autenticado o está baneado, devuelve un diccionario de error y un código de estado 401.
    - Si el parámetro `offset` no es un número, devuelve un diccionario de error y un código de estado 400.
    - Si el usuario está autenticado y el parámetro `offset` es válido, devuelve los mensajes solicitados (lista o diccionario) con el código de estado 200.
    - En caso de error interno, devuelve un diccionario de error y un código de estado 500.
    """
    try:
        if 'nombre' not in session or userBanned(session['nombre']):
            return {"error" : "Acceso no autorizado"}, 401
        
        offset = int(request.args.get('offset', 0))
        if offset < 0:
            offset = 0
            
        return get_messages(offset=offset)
    except ValueError:
        return {"error" : "Offset debe ser un número"}, 400
    except Exception as e:
        logger.error(f"Error loading messages: {e}", exc_info=True)
        return {"error" : "Error al cargar mensajes"}, 500

@app.route("/get_info", methods=["GET"])
def get_info() -> Union[tuple[dict[str, str], int], tuple[dict, int]]:
    """
    Endpoint para obtener información del sistema y estadísticas.
    Solo accesible para administradores (role >= 10).

    Returns:
         - Si el acceso es autorizado:
            - Un diccionario con información del sistema y estadísticas (`cpu` y `memory`).
            - Código de estado HTTP 200.
        - Si el acceso no está autorizado:
            - Un diccionario con un mensaje de error ("Acceso no autorizado").
            - Código de estado HTTP 401.
        - En caso de error en la obtención de información:
            - Un diccionario con un mensaje de error ("Error al obtener información").
            - Código de estado HTTP 500.
    """
    try:
        if 'nombre' not in session or session['role'] < 10:
            return {"error" : "Acceso no autorizado"}, 401
        
        data = db_get_info()
        data['cpu'] = psutil.cpu_percent()  # Uso de CPU
        data['memory'] = round(psutil.Process().memory_percent() * 100, 2)  # Uso de memoria
        return data, 200
    except Exception as e:
        logger.error(f"Error getting info: {e}", exc_info=True)
        return {"error" : "Error al obtener información"}, 500

@app.route("/login", methods=["GET", "POST"])
def login() -> Union[Response, str]:
    """
    Maneja el inicio de sesión de usuarios.

    GET: Muestra el formulario de login. Si el usuario ya está autenticado, redirige al chat.

    POST: Procesa el formulario y autentica al usuario. Si las credenciales son correctas,
          redirige al chat. Si el usuario está baneado, muestra el tiempo restante para la expulsión.
          Si hay un error, muestra un mensaje adecuado.

    Returns:
        Union[Response, str]:
         - Si el usuario es autenticado correctamente, redirige a la página de chat.
         - Si hay un error, muestra el formulario de login con un mensaje de error.
    """
    error = None
    timer = None
    try:
        if 'nombre' in session:
            return redirect(url_for('chat'))
        if request.method == 'POST':
            nombre = request.form.get('nombre', '').strip()
            password = request.form.get('pass', '')
            
            if not nombre or not password:
                error = "Nombre y contraseña son necesarios"
                return render_template('login.html', error=error)
                
            try:
                if any(usuario['name'] == nombre for usuario in get_usuarios_online()):
                        error = "El usuario ya está conectado"
                else:    
                    usuario = validate_credentials(nombre, password)
                    if(usuario):
                        if usuario['banned_until'] and datetime.now() < usuario['banned_until']:
                            error = "has sido expulsado del chat hasta:"
                            timer = usuario['banned_until'].strftime("%H:%M:%S, %m/%d/%Y")
                            return render_template('login.html', error=error, timer=timer)
                        else:
                            session['nombre'] = nombre
                            session['role'] = usuario['role']
                            return redirect(url_for('chat'))
                    else:
                        error = "Nombre o contraseña incorrectos"
            except Exception as e:
                logger.error(f"Error during login: {e}", exc_info=True)
                error = "Error durante el inicio de sesión. Inténtalo de nuevo más tarde"
    except Exception as e:
        logger.error(f"Unexpected error in login route: {e}", exc_info=True)
        error = "Error inesperado. Inténtalo de nuevo más tarde"
        
    return render_template('login.html', error=error, timer=timer)

@app.route("/logout")
def logout() -> Response:
    """
    Cierra la sesión del usuario actual y redirige a la página de login.

    Si la sesión del usuario está activa, se elimina su información de sesión y se le redirige al formulario de inicio de sesión. En caso de error, también se redirige al login.

    Returns:
        Response: Un objeto de respuesta que redirige a la página de login.
    """
    try:
        if 'nombre' in session:
            session.clear()
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Error during logout: {e}", exc_info=True)
        return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register() -> Union[Response, str]:
    """
    Maneja el registro de nuevos usuarios.
    GET: Muestra el formulario de registro.
    POST: Procesa el formulario y crea un nuevo usuario si los datos son válidos.

    Returns:
        Union[Response, str]:
         - Si la solicitud es GET, devuelve el formulario de registro (plantilla HTML).
         - Si la solicitud es POST, redirige al inicio de sesión si el registro es exitoso o muestra el formulario con un mensaje de error si hay un problema.
    """
    error = None
    try:
        if 'nombre' in session:
            return redirect(url_for('chat'))
        
        if request.method == 'POST':
            nombre = request.form.get('nombre', '').strip()
            password = request.form.get('pass', '')
            repetirPass = request.form.get('passrepeat', '')

            # Validación de datos de registro
            if not nombre or not password or not repetirPass:
                error = "Todos los campos son necesarios"
            elif len(nombre) < 3:
                error = "El nombre es demasiado corto"
            elif username_exists(nombre):
                error = "El nombre no está disponible"
            elif len(password) < 5:
                error = "La contraseña es demasiado corta"
            elif not (any(c.isalpha() for c in password) and any(c.isdigit() for c in password)):
                error = "La contraseña debe contener al menos una letra y un número"
            elif password != repetirPass:
                error = "Las contraseñas no coinciden"
            else:
                try:
                    register_user(nombre, password)
                    flash("Usuario registrado con éxito", 'success')
                    return redirect(url_for('login'))
                except Exception as e:
                    logger.error(f"Error registering user: {e}", exc_info=True)
                    error = "Error durante el registro. Inténtalo de nuevo más tarde"
    except Exception as e:
        logger.error(f"Unexpected error in register route: {e}", exc_info=True)
        error = "Error inesperado. Inténtalo de nuevo más tarde"

    return render_template('register.html', error=error)

@app.route("/search_users", methods=["GET"])
def search_users() -> tuple[dict[str, str] or list, int]:
    """
    Endpoint para buscar usuarios por nombre.
    Solo accesible para administradores (role >= 10).

    Query params:
        termino (str): Término de búsqueda para filtrar usuarios.

    Returns:
        tuple[dict[str, str] or list, int]:
            - dict[str, str] si ocurre un error (por ejemplo, acceso no autorizado, falta de término de búsqueda o error en el servidor).
            - list si la búsqueda es exitosa (una lista de usuarios encontrados).
            - int: Código de estado HTTP.
                - 200 si la búsqueda es exitosa.
                - 401 si el usuario no está autenticado o no tiene el rol adecuado.
                - 400 si no se proporciona el término de búsqueda.
                - 500 si ocurre un error inesperado.
    """
    try:
        if 'nombre' not in session or session['role'] < 10:
            return {"error" : "Acceso no autorizado"}, 401

        termino = request.args.get('termino', '').strip()
        if not termino:
            return {"error" : "Nombre de usuario requerido"}, 400

        usuarios = db_search_users(termino)

        return usuarios, 200
    except Exception as e:
        logger.error(f"Error searching users: {e}", exc_info=True)
        return {"error" : "Error al buscar usuarios"}, 500

@app.route("/change_role", methods=["POST"])
def change_role() -> tuple[dict[str, str], int]:
    """
    Endpoint para cambiar el rol de un usuario.
    Solo accesible para administradores (role >= 10).
    
    JSON body:
        user (int): ID del usuario
        role (int): Nuevo rol a asignar (0-10)

    Returns:
        tuple[dict[str, str], int]:
            - dict[str, str]: Mensaje descriptivo del resultado de la operación.
            - int: Código de estado HTTP (por ejemplo, 200 para éxito, 400 para error de solicitud, 401 para acceso no autorizado, 500 para error en el servidor).

    """
    try:
        if 'nombre' not in session or session['role'] < 10:
            return {"error" : "Acceso no autorizado"}, 401
        
        data = request.json
        if not data:
            return {"error" : "Datos no proporcionados"}, 400
            
        user_id = data.get('user')
        new_role = data.get('role')
        
        if user_id is None or new_role is None:
            return {"error" : "Datos incompletos"}, 400
            
        try:
            new_role = int(new_role)
            if new_role < 0 or new_role > 10:
                return {"error" : "Rol inválido"}, 400
        except ValueError:
            return {"error" : "Rol debe ser un número"}, 400
        
        success = db_change_role(user_id, new_role)
        if success:
            return {"success" : "Rol cambiado con éxito"}, 200
        else:
            return {"error" : "Error al cambiar el rol"}, 500
    except Exception as e:
        logger.error(f"Error changing role: {e}", exc_info=True)
        return {"error" : "Error al cambiar el rol"}, 500

@app.route("/unban_user", methods=["POST"])
def unban_user() -> tuple[dict[str, str], int]:
    """
    Endpoint para desbanear a un usuario.
    Solo accesible para administradores (role >= 10).
    
    JSON body:
        user (int): ID del usuario a desbanear.

    Returns:
        tuple[dict[str, str], int]:
            - Si el usuario es desbaneado con éxito:
              {"success" : "Usuario desbaneado con éxito"}, 200.
            - Si los datos no son proporcionados o están incompletos:
              {"error" : "Datos no proporcionados" o "Datos incompletos"}, 400.
            - Si el usuario no tiene acceso:
              {"error" : "Acceso no autorizado"}, 401.
            - Si hay un error al desbanear al usuario:
              {"error" : "Error al desbanear el usuario"}, 500.
    """
    try:
        if 'nombre' not in session or session['role'] < 10:
            return {"error" : "Acceso no autorizado"}, 401
        
        data = request.json
        if not data:
            return {"error" : "Datos no proporcionados"}, 400
            
        user_id = data.get('user')
        if user_id is None:
            return {"error" : "Datos incompletos"}, 400
        
        success = db_unban_user(user_id)
        if success:
            return {"success" : "Usuario desbaneado con éxito"}, 200
        else:
            return {"error" : "Error al desbanear el usuario"}, 500
    except Exception as e:
        logger.error(f"Error unbanning user: {e}", exc_info=True)
        return {"error" : "Error al desbanear el usuario"}, 500 