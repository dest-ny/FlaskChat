from app import mysql, flask_bcrypt


def db_insert(sql, args):
    try:
        conn = mysql.get_db()
        cur = conn.cursor()
        cur.execute(sql, args)
        conn.commit()
    except Exception as e:
        print("Database insertion error: ", e)
        conn.rollback()


def username_exists(user):
    try:
        conn = mysql.get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE name = %s", (user,))
        result = cur.fetchone()
        if result:
                return True
        return False
    except Exception as e:
        print(f"Error comprobando si {user} existe: ", e)
        return False

def validate_credentials(user, password):
    try:
        conn = mysql.get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE name = %s", (user,))
        result = cur.fetchone()
        if result:
            if flask_bcrypt.check_password_hash(result['password'], password):
                return result
        return {}
    except Exception as e:
        print(f"Error validando la contraseña para {user}: ", e)
        return {}

def register_user(user, password):
    hashedpw = flask_bcrypt.generate_password_hash(password)
    db_insert("INSERT INTO users(name, password) VALUES (%s, %s)", (user, hashedpw))

def store_message(user, message):
    try:
        conn = mysql.get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE name = %s", (user,))
        res = cur.fetchone()
        if res:
            cur.execute("INSERT INTO messages (sender, content) VALUES (%s, %s)", (res['id'], message))
            conn.commit()
            cur.execute("SELECT sender, name, content, DATE_FORMAT(timestamp, '%d-%m-%Y %I:%i %p') AS fecha_formateada FROM users JOIN messages on(users.id = sender) WHERE messages.id = LAST_INSERT_ID()")
            message = cur.fetchone()
            if message:
                return message
    except Exception as e:
        print("Error guardando el mensaje: ", e)
        conn.rollback()
    return {}


def get_messages():
    try:
        conn = mysql.get_db()
        cur = conn.cursor()
        cur.execute("SELECT sender, content, name, DATE_FORMAT(timestamp, '%k:%i | %d-%m-%Y') AS fecha_formateada FROM users JOIN messages on(users.id=sender) ORDER BY messages.id ASC")
        res = cur.fetchall()
        if res:
            for r in res:
                r['content'] = r['content'].decode('utf-8')
            return res
        else:
            return {}
    except Exception as e:
        print("Error sacando los mensajes: ", e)

def get_usuarios_online():
    try:
        conn = mysql.get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, online, role FROM users WHERE online = %s", (True,))
        res = cur.fetchall()
        if res:
            return res
        else:
            return {}
    except Exception as e:
        print("Error en la consulta de usuarios online: ", e)

def get_usuario(id=None, name=None):
    try:
        conn = mysql.get_db()
        cur = conn.cursor()
        if id:
            cur.execute("SELECT id, name, online, role, banned_until FROM users WHERE id = %s", (id,))
        elif name:
            cur.execute("SELECT id, name, online, role, banned_until FROM users WHERE name = %s", (name,))
        else:
            return
        
        res = cur.fetchone()
        if res:
            return res
        else:
            return {}
    except Exception as e:
        print("Error en la consulta de usuario: ", e)

def set_online_status(name, status):
    try:
        conn = mysql.get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET online = %s WHERE name = %s", (status, name))
        conn.commit()
    except Exception as e:
        print("Error cambiando el estado del usuario: ", e)
        
def db_timeout_user(id, time):
    try:
        conn = mysql.get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET banned_until = %s WHERE id = %s", (time, id))
        conn.commit()
    except Exception as e:
        print("Error actualizando el banned_until en la tabla de usuarios: ", e)