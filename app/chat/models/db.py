from app import mysql, flask_bcrypt
from contextlib import contextmanager
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connection pool management
@contextmanager
def get_db_cursor():
    conn = None
    cur = None
    try:
        conn = mysql.get_db()
        cur = conn.cursor()
        yield cur
        # Auto-commit successful operations
        conn.commit()
    except Exception as e:
        logger.error(f"Database error: {e}", exc_info=True)
        if conn:
            conn.rollback()
        raise
    finally:
        # Ensure cursor is closed even if an exception occurs
        if cur:
            cur.close()

def db_insert(sql, args):
    try:
        with get_db_cursor() as cur:
            cur.execute(sql, args)
            # No need to commit here as it's handled in the context manager
    except Exception as e:
        logger.error(f"Database insertion error: {e}", exc_info=True)


def username_exists(user):
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE name = %s", (user,))
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
                # Get the inserted message with formatted date
                cur.execute("""
                    SELECT sender, name, content, DATE_FORMAT(timestamp, '%k:%i | %d/%m/%Y') AS fecha_formateada 
                    FROM users JOIN messages on(users.id = sender) 
                    WHERE messages.id = LAST_INSERT_ID()
                """)
                message = cur.fetchone()
                if message:
                    # Decode content if it's in bytes format
                    if isinstance(message['content'], bytes):
                        message['content'] = message['content'].decode('utf-8')
                    return message
    except Exception as e:
        logger.error(f"Error saving message: {e}", exc_info=True)
    return {}

def get_messages(limit=50, offset=0):
    try:
        with get_db_cursor() as cur:
            sql = """
                SELECT messages.id, sender, content, name, 
                       DATE_FORMAT(timestamp, '%%k:%%i | %%d/%%m/%%Y') AS fecha_formateada 
                FROM users JOIN messages on(users.id=sender) 
                ORDER BY messages.id DESC LIMIT %s OFFSET %s
            """
            cur.execute(sql, (limit, offset))
            res = cur.fetchall()
            if res:
                # Batch process all message content decoding
                for r in res:
                    if isinstance(r['content'], bytes):
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

def db_start():
    try:
        with get_db_cursor() as cur:
            cur.execute("UPDATE users SET online = 0")
            # No need to commit here as it's handled in the context manager
    except Exception as e:
        logger.error(f"Error updating user status: {e}", exc_info=True)

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
            # No need to commit here as it's handled in the context manager
    except Exception as e:
        logger.error(f"Error updating user status: {e}", exc_info=True)
        
def db_timeout_user(id, time):
    try:
        with get_db_cursor() as cur:
            cur.execute("UPDATE users SET banned_until = %s, online = 0 WHERE id = %s", (time, id))
            # No need to commit here as it's handled in the context manager
    except Exception as e:
        logger.error(f"Error updating banned_until: {e}", exc_info=True)

def db_get_info():
    try:
        with get_db_cursor() as cur:
            # Optimize by using a single query
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM users) as usercount,
                    (SELECT COUNT(*) FROM messages) as messagecount
            """)
            result = cur.fetchone()
            if result:
                return {
                    "users": result['usercount'],
                    "messages": result['messagecount']
                }
            return {"users": 0, "messages": 0}
    except Exception as e:
        logger.error(f"Error fetching database info: {e}", exc_info=True)
        return {"users": 0, "messages": 0}
    
def db_search_users(termino):
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT u.id, u.name, u.role, u.online, u.banned_until, 
                       COUNT(m.id) as message_count 
                FROM users u
                LEFT JOIN messages m ON u.id = m.sender
                WHERE LOWER(u.name) LIKE LOWER(%s)
                GROUP BY u.id, u.name, u.role, u.online, u.banned_until
            """, (f"%{termino}%",))
            res = cur.fetchall()
            return res if res else {}
    except Exception as e:
        logger.error(f"Error fetching users: {e}", exc_info=True)
        return {}

def db_delete_all_messages():
    try:
        with get_db_cursor() as cur:
            cur.execute("DELETE FROM messages")
            # No need to commit here as it's handled in the context manager
    except Exception as e:
        logger.error(f"Error deleting messages: {e}", exc_info=True)

def db_change_role(user_id, new_role):
    try:
        with get_db_cursor() as cur:
            cur.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
            # No need to commit here as it's handled in the context manager
            return True
    except Exception as e:
        logger.error(f"Error changing role: {e}", exc_info=True)
        return False

def db_unban_user(user_id):
    try:
        with get_db_cursor() as cur:
            cur.execute("UPDATE users SET banned_until = NULL WHERE id = %s", (user_id,))
            # No need to commit here as it's handled in the context manager
            return True
    except Exception as e:
        logger.error(f"Error unbanning user: {e}", exc_info=True)
        return False    
