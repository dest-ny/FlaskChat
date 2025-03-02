# Controlador principal de rutas para la aplicación de chat
from app import app
from flask import render_template, session, url_for, request, redirect, flash, jsonify
from app.chat.models.db import *
from datetime import datetime
import psutil
import logging

logger = logging.getLogger(__name__)

def userBanned(name):
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
def chat():
    """
    Ruta principal que muestra la interfaz de chat.
    Redirige al login si el usuario no ha iniciado sesión o está baneado.
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
def load_messages():
    """
    Endpoint para cargar mensajes del chat con paginación.
    Requiere que el usuario esté autenticado y no baneado.
    
    Query params:
        offset (int): Número de mensajes a saltar para la paginación
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
def get_info():
    """
    Endpoint para obtener información del sistema y estadísticas.
    Solo accesible para administradores (role >= 10).
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
def login():
    """
    Maneja el inicio de sesión de usuarios.
    GET: Muestra el formulario de login
    POST: Procesa el formulario y autentica al usuario
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
def logout():
    """
    Cierra la sesión del usuario actual y redirige a la página de login.
    """
    try:
        if 'nombre' in session:
            session.clear()
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Error during logout: {e}", exc_info=True)
        return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Maneja el registro de nuevos usuarios.
    GET: Muestra el formulario de registro
    POST: Procesa el formulario y crea un nuevo usuario si los datos son válidos
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
def search_users():
    """
    Endpoint para buscar usuarios por nombre.
    Solo accesible para administradores (role >= 10).
    
    Query params:
        termino (str): Término de búsqueda para filtrar usuarios
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
def change_role():
    """
    Endpoint para cambiar el rol de un usuario.
    Solo accesible para administradores (role >= 10).
    
    JSON body:
        user (int): ID del usuario
        role (int): Nuevo rol a asignar (0-10)
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
def unban_user():
    """
    Endpoint para desbanear a un usuario.
    Solo accesible para administradores (role >= 10).
    
    JSON body:
        user (int): ID del usuario a desbanear
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