from app import app
from flask import render_template, session, url_for, request, redirect, flash
from app.chat.models.db import *

@app.route("/")
def chat():
    if 'nombre' in session:
        return render_template('index.html', lista_mensajes=get_messages())
    else:
        return redirect(url_for('login'))
    
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if 'nombre' in session:
        return redirect(url_for('chat'))
    if request.method == 'POST':
        nombre = request.form['nombre']
        password = request.form['pass']
        result = validate_credentials(nombre, password)
        if(result):
            session['nombre'] = nombre
            session['role'] = result['role']
            return redirect(url_for('chat'))
        else:
            error = "Nombre o contraseña incorrectos"
    return render_template('login.html', error=error)

@app.route("/logout")
def logout():
    if 'nombre' in session:
        session.pop('nombre', None)
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
        if len(nombre.strip()) >= 3:
            if not username_exists(nombre):
                if len(password) > 4:
                    l = any(c.isalpha() for c in password)
                    n = any(c.isalpha() for c in password)
                    if l and n:
                        if password == repetirPass:
                            register_user(nombre, password)
                            flash("Usuario registrado con éxito", 'success')
                            return redirect(url_for('chat'))
                        else:
                            error = "Contraseñas no coinciden"
                    else:
                        error = "Contraseña inválida (no contiene numero o letra)"
                else:
                    error = "Contraseña demasiado corta"
            else:
                error = "Nombre no disponible"
        else:
            error = "Nombre demasiado corto"
    return render_template('register.html', error = error)