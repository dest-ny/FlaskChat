from app import app
from flask import render_template, session, url_for, request, redirect, flash
from app.chat.models.db import *
from datetime import datetime

def userBanned(name):
    usuario = get_usuario(name=name)
    if usuario:
        if usuario['banned_until'] and datetime.now() < usuario['banned_until']:
            return True
    return False

@app.route("/")
def chat():
    if 'nombre' in session:
        if userBanned(session['nombre']):
            session.clear()
            flash("HAS SIDO EXPULSADO DEL CHAT", 'error')
            return redirect(url_for('login'))
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

@app.route("/load_messages", methods=["GET"])
def load_messages():
    if 'nombre' not in session or userBanned(session['nombre']):
        return {"error" : "Acceso no autorizado"}, 401
    
    offset = int(request.args.get('offset', 0))
    return get_messages(offset = offset)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    timer = None
    if 'nombre' in session:
        return redirect(url_for('chat'))
    if request.method == 'POST':
        nombre = request.form['nombre']
        password = request.form['pass']
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
            error = "Error durante el inicio de sesión. Inténtalo de nuevo más tarde"
    return render_template('login.html', error=error)

@app.route("/logout")
def logout():
    if 'nombre' in session:
        session.clear()
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if 'nombre' in session:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        password = request.form['pass']
        repetirPass = request.form['passrepeat']

        try:
            if len(nombre.strip()) < 3:
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
                register_user(nombre, password)
                flash("Usuario registrado con éxito", 'success')
                return redirect(url_for('login'))
        except Exception as e:
            error = "Error durante el registro. Inténtalo de nuevo más tarde"

    return render_template('register.html', error = error)