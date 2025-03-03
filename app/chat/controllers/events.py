# Controlador de eventos de Socket.IO para la comunicación en tiempo real
from app import socketio
from flask import session, render_template
from app.chat.models.db import * 
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@socketio.on('connect')
def conectado():
    """
    Manejador del evento de conexión de Socket.IO.
    Se ejecuta cuando un usuario se conecta al chat.
    Verifica si el usuario está baneado y notifica a todos los usuarios de la conexión.
    """
    try:
        if 'nombre' not in session:
            return
        
        user = get_usuario(name=session['nombre'])
        if user:
            if user['banned_until'] and datetime.now() < user['banned_until']:
                socketio.emit("force_disconnect", session['nombre'])  # Desconecta al usuario si está baneado
            else:
                mensaje = {
                    'category' : "chat_join",
                    'name' : f"{session['nombre']}",
                    'content': "se ha unido a la sala!",
                    }
                set_online_status(session['nombre'], True)  # Marca al usuario como conectado en la BD
                socketio.emit('estado', mensaje)  # Notifica a todos los usuarios
                socketio.emit("usuarios_online", get_usuarios_online())  # Actualiza la lista de usuarios conectados
    except Exception as e:
        logger.error(f"Error in connect event: {e}", exc_info=True)
    
@socketio.on('disconnect')
def desconectado():
    """
    Manejador del evento de desconexión de Socket.IO.
    Se ejecuta cuando un usuario se desconecta del chat.
    Actualiza el estado del usuario y notifica a todos los usuarios de la desconexión.
    """
    try:
        if 'nombre' not in session:
            return
            
        user = get_usuario(name=session['nombre'])
        if user:
            set_online_status(session['nombre'], False)  # Marca al usuario como desconectado en la BD
            if not (user['banned_until'] and datetime.now() < user['banned_until']):         
                mensaje = {
                    'category' : "chat_leave",
                    'name' : f"{session['nombre']}",
                    'content': "ha salido de la sala!",
                    }
                socketio.emit('estado', mensaje)  # Notifica a todos los usuarios
                socketio.emit("usuarios_online", get_usuarios_online())  # Actualiza la lista de usuarios conectados
    except Exception as e:
        logger.error(f"Error in disconnect event: {e}", exc_info=True)
    
@socketio.on("mensaje")
def recibir_mensaje(msg: str):
    """
    Manejador del evento de mensaje de Socket.IO.
    Se ejecuta cuando un usuario envía un mensaje al chat.
    Almacena el mensaje en la BDD y lo reenvía a todos los usuarios.
    
    Args:
        msg (str): Contenido del mensaje enviado por el usuario
    """
    try:
        if 'nombre' not in session: 
            return
        message = store_message(session['nombre'], msg)  # Guarda el mensaje en la BD
        socketio.emit("mensaje", message)  # Reenvía el mensaje a todos los usuarios
    except Exception as e:
        logger.error(f"Error in mensaje event: {e}", exc_info=True)
    
@socketio.on("timeout_user")
def timeout_user(data: dict):
    """
    Manejador del evento para banear temporalmente a un usuario.
    Solo puede ser ejecutado por moderadores (role >= 5) contra usuarios de menor rango.
    
    Args:
        data (dict): Diccionario con los datos del baneo.
            - user (int): ID del usuario a banear.
            - duration (int): Duración del baneo en minutos, -1 para baneo permanente.
    """
    try:
        if 'nombre' not in session:
            return
            
        usuario = get_usuario(data['user'])
        if not usuario:
            return
            
        # Verifica que el usuario tenga permisos suficientes para banear.
        if session['role'] >= 5 and session['role'] > usuario['role']:
            time_until = 0
            mensaje = {}
            print(data['duration'])
            if data['duration'] != -1:
                # Baneo temporal
                minutos = timedelta(minutes=data['duration'])
                time_until = datetime.now() + minutos
                mensaje = {
                        'category' : "chat_ban",
                        'name' : usuario['name'],
                        'content': f"ha sido expulsado de la sala hasta: {time_until.strftime('%d/%m/%Y - %H:%M')}",
                        }
            else:
                # Baneo permanente.
                time_until = datetime.max
                print(time_until)
                mensaje = {
                        'category' : "chat_ban",
                        'name' : usuario['name'],
                        'content': f"ha sido vetado de la sala para siempre!",
                        }
            db_timeout_user(data['user'], time_until)  # Actualiza el estado de baneo en la BD.
            set_online_status(usuario['name'], 0)  # Marca al usuario como desconectado.
            socketio.emit("force_disconnect", usuario['name'])  # Fuerza la desconexión del usuario.
            socketio.emit('estado', mensaje)  # Notifica a todos los usuarios.
            socketio.emit("usuarios_online", get_usuarios_online())  # Actualiza la lista de usuarios conectados.
        else:
            logger.warning(f"Usuario {session['nombre']} ha intentado una acción con permisos insuficientes")
    except Exception as e:
        logger.error(f"Error in timeout_user event: {e}", exc_info=True)

@socketio.on("clear_messages")
def clear_messages():
    """
    Manejador del evento para borrar todos los mensajes del chat.
    Solo puede ser ejecutado por administradores (role >= 10).
    """
    try:
        if 'nombre' not in session:
            return
            
        if session['role'] >= 10:
            db_delete_all_messages()  # Borra todos los mensajes de la BD.
            socketio.emit("clear_messages")  # Notifica a todos los usuarios para limpiar sus chats.
        else:
            logger.warning(f"Usuario {session['nombre']} ha intentado una acción con permisos insuficientes")
    except Exception as e:
        logger.error(f"Error in clear_messages event: {e}", exc_info=True)

