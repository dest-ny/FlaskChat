from app import socketio
from flask import session

@socketio.on('connect')
def conectado():
    socketio.emit('estado', {
        'join' : 1,
        'nombre' : f"{session['nombre']}",
        'msg': "se ha unido a la sala!"
    })

@socketio.on("mensaje")
def recibir_mensaje(msg):
    socketio.emit("mensaje", {
        'msg':msg,
        'sender':session['nombre']
    })