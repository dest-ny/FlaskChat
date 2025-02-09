from app import mysql, flask_bcrypt
from contextlib import contextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def get_db_cursor():
    conn = None
    cur = None
    try:
        conn = mysql.get_db()
        cur = conn.cursor()
        yield cur
    except Exception as e:
        logger.error(f"Database error: {e}", exc_info=True)
        if conn:
            conn.rollback()
        raise

def db_insert(sql, args):
    try:
        with get_db_cursor() as cur:
            cur.execute(sql, args)
            cur.connection.commit()
    except Exception as e:
        logger.error(f"Database insertion error: {e}", exc_info=True)


def username_exists(user):
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM users WHERE name = %s", (user,))
            result = cur.fetchone()
            return bool(result)
    except Exception as e:
        logger.error(f"Error checking if {user} exists: {e}", exc_info=True)
        return False

def validate_credentials(user, password):
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM users WHERE name = %s", (user,))
            result = cur.fetchone()
            if result and flask_bcrypt.check_password_hash(result['password'], password):
                return result
            logger.warning(f"Validation failed for user {user}")
            return {}
    except Exception as e:
        logger.error(f"Error validating password for {user}: {e}", exc_info=True)
        return {}

def register_user(user, password):
    hashedpw = flask_bcrypt.generate_password_hash(password).decode('utf-8')
    db_insert("INSERT INTO users(name, password) VALUES (%s, %s)", (user, hashedpw))

def store_message(user, message):
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT id FROM users WHERE name = %s", (user,))
            res = cur.fetchone()
            if res:
                cur.execute("INSERT INTO messages (sender, content) VALUES (%s, %s)", (res['id'], message))
                cur.connection.commit()
                cur.execute("SELECT sender, name, content, DATE_FORMAT(timestamp, '%k:%i | %d-%m-%Y') AS fecha_formateada FROM users JOIN messages on(users.id = sender) WHERE messages.id = LAST_INSERT_ID()")
                message = cur.fetchone()
                if message:
                    return message
    except Exception as e:
        logger.error(f"Error saving message: {e}", exc_info=True)
        # No need to call rollback here; it's handled in the context manager
    return {}

def get_messages():
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT sender, content, name, DATE_FORMAT(timestamp, '%k:%i | %d-%m-%Y') AS fecha_formateada FROM users JOIN messages on(users.id=sender) ORDER BY messages.id ASC")
            res = cur.fetchall()
            if res:
                for r in res:
                    r['content'] = r['content'].decode('utf-8')
                return res
            return {}
    except Exception as e:
        logger.error(f"Error fetching messages: {e}", exc_info=True)
        return {}

def get_usuarios_online():
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT id, name, online, role FROM users WHERE online = %s", (True,))
            res = cur.fetchall()
            return res if res else {}
    except Exception as e:
        logger.error(f"Error fetching online users: {e}", exc_info=True)
        return {}

def get_usuario(id=None, name=None):
    try:
        with get_db_cursor() as cur:
            if id:
                cur.execute("SELECT id, name, online, role, banned_until FROM users WHERE id = %s", (id,))
            elif name:
                cur.execute("SELECT id, name, online, role, banned_until FROM users WHERE name = %s", (name,))
            else:
                return {}
            res = cur.fetchone()
            return res if res else {}
    except Exception as e:
        logger.error(f"Error fetching user: {e}", exc_info=True)
        return {}

def set_online_status(name, status):
    try:
        with get_db_cursor() as cur:
            cur.execute("UPDATE users SET online = %s WHERE name = %s", (status, name))
            cur.connection.commit()
    except Exception as e:
        logger.error(f"Error updating user status: {e}", exc_info=True)
        
def db_timeout_user(id, time):
    try:
        with get_db_cursor() as cur:
            cur.execute("UPDATE users SET banned_until = %s WHERE id = %s", (time, id))
            cur.connection.commit()
    except Exception as e:
        logger.error(f"Error updating banned_until: {e}", exc_info=True)