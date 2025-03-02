from app import socketio
from flask import session, render_template
from app.chat.models.db import * 
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@socketio.on('connect')
def conectado():
    try:
        if 'nombre' not in session:
            return
        
        user = get_usuario(name=session['nombre'])
        if user:
            if user['banned_until'] and datetime.now() < user['banned_until']:
                socketio.emit("force_disconnect", session['nombre'])  
            else:
                mensaje = {
                    'category' : "chat_join",
                    'name' : f"{session['nombre']}",
                    'content': "se ha unido a la sala!",
                    }
                set_online_status(session['nombre'], True)
                socketio.emit('estado', mensaje)
                socketio.emit("usuarios_online", get_usuarios_online())
    except Exception as e:
        logger.error(f"Error in connect event: {e}", exc_info=True)
    
@socketio.on('disconnect')
def desconectado():
    try:
        if 'nombre' not in session:
            return
            
        user = get_usuario(name=session['nombre'])
        if user:
            set_online_status(session['nombre'], False)
            if not (user['banned_until'] and datetime.now() < user['banned_until']):         
                mensaje = {
                    'category' : "chat_leave",
                    'name' : f"{session['nombre']}",
                    'content': "ha salido de la sala!",
                    }
                socketio.emit('estado', mensaje)
                socketio.emit("usuarios_online", get_usuarios_online())
    except Exception as e:
        logger.error(f"Error in disconnect event: {e}", exc_info=True)
    
@socketio.on("mensaje")
def recibir_mensaje(msg):
    try:
        if 'nombre' not in session: 
            return
        message = store_message(session['nombre'], msg)
        socketio.emit("mensaje", message)
    except Exception as e:
        logger.error(f"Error in mensaje event: {e}", exc_info=True)
    
@socketio.on("timeout_user")
def timeout_user(data):
    try:
        if 'nombre' not in session:
            return
            
        usuario = get_usuario(data['user'])
        if not usuario:
            return
            
        if session['role'] >= 5 and session['role'] > usuario['role']:
            time_until = 0
            mensaje = {}
            print(data['duration'])
            if data['duration'] != -1:
                minutos = timedelta(minutes=data['duration'])
                time_until = datetime.now() + minutos
                mensaje = {
                        'category' : "chat_ban",
                        'name' : usuario['name'],
                        'content': f"ha sido expulsado de la sala hasta: {time_until.strftime('%d/%m/%Y - %H:%M')}",
                        }
            else:
                time_until = datetime.max
                print(time_until)
                mensaje = {
                        'category' : "chat_ban",
                        'name' : usuario['name'],
                        'content': f"ha sido vetado de la sala para siempre!",
                        }
            db_timeout_user(data['user'], time_until)
            set_online_status(usuario['name'], 0)
            socketio.emit("force_disconnect", usuario['name'])
            socketio.emit('estado', mensaje)
            socketio.emit("usuarios_online", get_usuarios_online())
        else:
            logger.warning(f"Usuario {session['nombre']} ha intentado una acción con permisos insuficientes")
    except Exception as e:
        logger.error(f"Error in timeout_user event: {e}", exc_info=True)

@socketio.on("clear_messages")
def clear_messages():
    try:
        if 'nombre' not in session:
            return
            
        if session['role'] >= 10:
            db_delete_all_messages()
            socketio.emit("clear_messages")
        else:
            logger.warning(f"Usuario {session['nombre']} ha intentado una acción con permisos insuficientes")
    except Exception as e:
        logger.error(f"Error in clear_messages event: {e}", exc_info=True)

