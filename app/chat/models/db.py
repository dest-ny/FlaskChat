from app import mysql, flask_bcrypt
from flask import g

def getConnection():
    if 'db' not in g:
        g.db = mysql.get_db()
    
    return g.db

def closeConnection(e=None):
    conn = g.pop('db', None)
    
    if conn is not None:
        conn.close()

def db_insert(sql, args):
    try:
        conn = getConnection()
        cur = conn.cursor()
        cur.execute(sql, args)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Database insertion error: ", e)
    finally:
        closeConnection()

def validate_credentials(user, password):
    try:
        conn = getConnection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE name = %s", (user,))
        result = cur.fetchone()
        if result:
            if flask_bcrypt.check_password_hash(result['password'], password):
                return True
        return False
    except Exception as e:
        print(f"Error validando la contraseña para {user}: ", e)
        return False
    finally:
        closeConnection()

