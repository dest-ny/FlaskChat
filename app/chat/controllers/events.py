from app import socketio
from flask import session, render_template
from app.chat.models.db import * 
from datetime import datetime, timedelta

@socketio.on('connect')
def conectado():
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
            socketio.emit('estado', render_template('includes/chatmessage.html', mensaje=mensaje))
            socketio.emit("usuarios_online", get_usuarios_online())
    else:
        return
    
@socketio.on('disconnect')
def desconectado():
    user = get_usuario(name=session['nombre'])
    if user:
        set_online_status(session['nombre'], False)
        if not (user['banned_until'] and datetime.now() < user['banned_until']):         
            mensaje = {
                'category' : "chat_leave",
                'name' : f"{session['nombre']}",
                'content': "ha salido de la sala!",
                }
            socketio.emit('estado', render_template('includes/chatmessage.html', mensaje=mensaje))
            socketio.emit("usuarios_online", get_usuarios_online())
    else:
        return
    
@socketio.on("mensaje")
def recibir_mensaje(msg):
    message = store_message(session['nombre'], msg)
    if message:
        message['content'] = message['content'].decode('utf-8')
    socketio.emit("mensaje", render_template('includes/chatmessage.html', mensaje=message))
    
@socketio.on("timeout_user")
def timeout_user(data):
    usuario = get_usuario(data['user'])
    if session['role'] >= 5 and session['role'] > usuario['role']:
        minutos = timedelta(minutes=data['duration'])
        time_until = datetime.now() + minutos
        db_timeout_user(data['user'], time_until)
        socketio.emit("force_disconnect", usuario['name'])
        mensaje = {
                'category' : "chat_ban",
                'name' : usuario['name'],
                'content': f"ha sido expulsado de la sala hasta: {time_until.strftime("%d/%m/%Y - %H:%M")}",
                }
        socketio.emit('estado', render_template('includes/chatmessage.html', mensaje=mensaje))
        socketio.emit("usuarios_online", get_usuarios_online())
    else:
        print(f"Usuario {session['role']} ha intentado una acción con permisos insuficientes")