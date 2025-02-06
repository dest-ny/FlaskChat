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
                return True
        return False
    except Exception as e:
        print(f"Error validando la contraseña para {user}: ", e)
        return False

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