from app import socketio
from flask import session, render_template
from app.chat.models.db import * 

@socketio.on('connect')
def conectado():
    mensaje = {
        'category' : "chat_join",
        'name' : f"{session['nombre']}",
        'content': "se ha unido a la sala!",
        }
    set_online_status(session['nombre'], True)
    socketio.emit('estado', render_template('includes/chatmessage.html', mensaje=mensaje))
    socketio.emit("usuarios_online", get_usuarios_online())
    
@socketio.on('disconnect')
def conectado():
    mensaje = {
        'category' : "chat_leave",
        'name' : f"{session['nombre']}",
        'content': "ha salido de la sala!",
        }
    set_online_status(session['nombre'], False)
    socketio.emit('estado', render_template('includes/chatmessage.html', mensaje=mensaje))
    socketio.emit("usuarios_online", get_usuarios_online())
    
@socketio.on("mensaje")
def recibir_mensaje(msg):
    message = store_message(session['nombre'], msg)
    if message:
        message['content'] = message['content'].decode('utf-8')
    socketio.emit("mensaje", render_template('includes/chatmessage.html', mensaje=message))