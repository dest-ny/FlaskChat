from app import socketio
from flask import session
from app.chat.models.db import * 

from . import USUARIOS

@socketio.on('connect')
def conectado():
    USUARIOS.append(session['nombre'])
    socketio.emit('estado', {
        'join' : 1,
        'nombre' : f"{session['nombre']}",
        'msg': "se ha unido a la sala!",
        'usuarios': USUARIOS
    })
    
@socketio.on('disconnect')
def conectado():
    USUARIOS.remove(session['nombre'])
    socketio.emit('estado', {
        'join' : 0,
        'nombre' : f"{session['nombre']}",
        'msg': "ha salido de la sala!",
        'usuarios': USUARIOS
    })
    
@socketio.on("mensaje")
def recibir_mensaje(msg):
    db_insert("INSERT INTO messages(sender, content) VALUES (%s, %s)", (1, msg))
    socketio.emit("mensaje", {
        'msg':msg,
        'sender':session['nombre']
    })