from app import app, flask_bcrypt
from flask import render_template, session, url_for, request, redirect, flash
from app.chat.models.db import validate_credentials, db_insert

from . import USUARIOS

@app.route("/")
def chat():
    if 'nombre' in session:
        return render_template('index.html', nombre = session["nombre"])
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
        if(validate_credentials(nombre, password)):
            print("true")
            session['nombre'] = nombre
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
    hashedpw = flask_bcrypt.generate_password_hash("admin").decode("utf-8")
    print(len(hashedpw))
    db_insert("INSERT INTO users(name, password) VALUES (%s, %s)", ("admin", hashedpw))
    return "register"