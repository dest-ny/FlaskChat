from app import app
from flask import render_template, session, url_for, request, redirect, flash

from . import USUARIOS

@app.route("/")
def index():
    if 'nombre' in session:
        return render_template('index.html', nombre = session["nombre"])
    else:
        return redirect(url_for('login'))
    
@app.route("/login", methods=["GET", "POST"])
def login():
    if 'nombre' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        if request.form['nombre'] in USUARIOS:
            error = "Usuario ya presente en la sala."
            flash(error)
            pass
        else:
            session['nombre'] = request.form['nombre']
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route("/logout")
def logout():
    if 'nombre' in session:
        session.pop('nombre', None)
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register():
    return "register"