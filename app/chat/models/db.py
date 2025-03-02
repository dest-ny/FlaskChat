# Módulo de acceso a la base de datos para la aplicación
from app import mysql, flask_bcrypt
from contextlib import contextmanager
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def get_db_cursor():
    """
    Administrador de contexto para obtener un cursor de base de datos.
    Maneja automáticamente la apertura y cierre de conexiones, así como
    las transacciones (commit/rollback).
    """
    conn = None
    cur = None
    try:
        conn = mysql.get_db()
        cur = conn.cursor()
        yield cur
        # Auto-commit para operaciones exitosas
        conn.commit()
    except Exception as e:
        logger.error(f"Database error: {e}", exc_info=True)
        if conn:
            conn.rollback()  # Revertir cambios en caso de error
        raise
    finally:
        # Asegurar que el cursor se cierre incluso si ocurre una excepción
        if cur:
            cur.close()

def db_insert(sql, args):
    """
    Función genérica para insertar datos en la base de datos.
    
    Args:
        sql (str): Consulta SQL con marcadores de posición
        args (tuple): Valores para los marcadores de posición
    """
    try:
        with get_db_cursor() as cur:
            cur.execute(sql, args)
            # No es necesario hacer commit aquí, se maneja en el administrador de contexto
    except Exception as e:
        logger.error(f"Database insertion error: {e}", exc_info=True)


def username_exists(user):
    """
    Verifica si un nombre de usuario ya existe en la base de datos.
    
    Args:
        user (str): Nombre de usuario a verificar
        
    Returns:
        bool: True si el usuario existe, False en caso contrario
    """
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE name = %s", (user,))
            result = cur.fetchone()
            return bool(result)
    except Exception as e:
        logger.error(f"Error checking if {user} exists: {e}", exc_info=True)
        return False

def validate_credentials(user, password):
    """
    Valida las credenciales de un usuario para el inicio de sesión.
    
    Args:
        user (str): Nombre de usuario
        password (str): Contraseña sin encriptar
        
    Returns:
        dict: Datos del usuario si las credenciales son válidas, diccionario vacío en caso contrario
    """
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
    """
    Registra un nuevo usuario en la base de datos.
    
    Args:
        user (str): Nombre de usuario
        password (str): Contraseña sin encriptar (será hasheada antes de almacenarla)
    """
    hashedpw = flask_bcrypt.generate_password_hash(password).decode('utf-8')
    db_insert("INSERT INTO users(name, password) VALUES (%s, %s)", (user, hashedpw))

def store_message(user, message):
    """
    Almacena un mensaje enviado por un usuario en la base de datos.
    
    Args:
        user (str): Nombre del usuario que envía el mensaje
        message (str): Contenido del mensaje
        
    Returns:
        dict: Datos del mensaje almacenado, incluyendo información del remitente
    """
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT id FROM users WHERE name = %s", (user,))
            res = cur.fetchone()
            if res:
                cur.execute("INSERT INTO messages (sender, content) VALUES (%s, %s)", (res['id'], message))
                # Obtener el mensaje insertado con fecha formateada
                cur.execute("""
                    SELECT sender, name, content, DATE_FORMAT(timestamp, '%k:%i | %d/%m/%Y') AS fecha_formateada 
                    FROM users JOIN messages on(users.id = sender) 
                    WHERE messages.id = LAST_INSERT_ID()
                """)
                message = cur.fetchone()
                if message:
                    # Decodificar el contenido si está en formato bytes
                    if isinstance(message['content'], bytes):
                        message['content'] = message['content'].decode('utf-8')
                    return message
    except Exception as e:
        logger.error(f"Error saving message: {e}", exc_info=True)
    return {}

def get_messages(limit=50, offset=0):
    """
    Obtiene mensajes del chat con paginación.
    
    Args:
        limit (int): Número máximo de mensajes a obtener
        offset (int): Número de mensajes a saltar para la paginación
        
    Returns:
        list: Lista de mensajes con información del remitente
    """
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
                # Procesar por lotes la decodificación de todos los contenidos de mensajes
                for r in res:
                    if isinstance(r['content'], bytes):
                        r['content'] = r['content'].decode('utf-8')
                return res
            return {}
    except Exception as e:
        logger.error(f"Error fetching messages: {e}", exc_info=True)
        return {}

def get_usuarios_online():
    """
    Obtiene la lista de usuarios conectados actualmente.
    
    Returns:
        list: Lista de usuarios conectados con su información
    """
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT id, name, online, role FROM users WHERE online = %s", (True,))
            res = cur.fetchall()
            return res if res else {}
    except Exception as e:
        logger.error(f"Error fetching online users: {e}", exc_info=True)
        return {}

def db_start():
    """
    Inicializa la base de datos al iniciar la aplicación.
    Marca a todos los usuarios como desconectados.
    """
    try:
        with get_db_cursor() as cur:
            cur.execute("UPDATE users SET online = 0")
            # No es necesario hacer commit aquí, se maneja en el administrador de contexto
    except Exception as e:
        logger.error(f"Error updating user status: {e}", exc_info=True)

def get_usuario(id=None, name=None):
    """
    Obtiene información de un usuario por ID o nombre.
    
    Args:
        id (int, optional): ID del usuario
        name (str, optional): Nombre del usuario
        
    Returns:
        dict: Datos del usuario si existe, diccionario vacío en caso contrario
    """
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
    """
    Actualiza el estado de conexión de un usuario.
    
    Args:
        name (str): Nombre del usuario
        status (bool): True si está conectado, False si está desconectado
    """
    try:
        with get_db_cursor() as cur:
            cur.execute("UPDATE users SET online = %s WHERE name = %s", (status, name))
            # No es necesario hacer commit aquí, se maneja en el administrador de contexto
    except Exception as e:
        logger.error(f"Error updating user status: {e}", exc_info=True)
        
def db_timeout_user(id, time):
    """
    Banea a un usuario hasta una fecha específica.
    
    Args:
        id (int): ID del usuario a banear
        time (datetime): Fecha hasta la que estará baneado
    """
    try:
        with get_db_cursor() as cur:
            cur.execute("UPDATE users SET banned_until = %s, online = 0 WHERE id = %s", (time, id))
            # No es necesario hacer commit aquí, se maneja en el administrador de contexto
    except Exception as e:
        logger.error(f"Error updating banned_until: {e}", exc_info=True)

def db_get_info():
    """
    Obtiene información estadística de la base de datos.
    
    Returns:
        dict: Diccionario con estadísticas (número de usuarios y mensajes)
    """
    try:
        with get_db_cursor() as cur:
            # Optimización usando una sola consulta
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
    """
    Busca usuarios por nombre.
    
    Args:
        termino (str): Término de búsqueda
        
    Returns:
        list: Lista de usuarios que coinciden con el término de búsqueda
    """
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
    """
    Elimina todos los mensajes de la base de datos.
    Solo debe ser utilizado por administradores.
    """
    try:
        with get_db_cursor() as cur:
            cur.execute("DELETE FROM messages")
            # No es necesario hacer commit aquí, se maneja en el administrador de contexto
    except Exception as e:
        logger.error(f"Error deleting messages: {e}", exc_info=True)

def db_change_role(user_id, new_role):
    """
    Cambia el rol de un usuario.
    
    Args:
        user_id (int): ID del usuario
        new_role (int): Nuevo rol a asignar
        
    Returns:
        bool: True si el cambio fue exitoso, False en caso contrario
    """
    try:
        with get_db_cursor() as cur:
            cur.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
            # No es necesario hacer commit aquí, se maneja en el administrador de contexto
            return True
    except Exception as e:
        logger.error(f"Error changing role: {e}", exc_info=True)
        return False

def db_unban_user(user_id):
    """
    Desbanea a un usuario.
    
    Args:
        user_id (int): ID del usuario a desbanear
        
    Returns:
        bool: True si el desbaneo fue exitoso, False en caso contrario
    """
    try:
        with get_db_cursor() as cur:
            cur.execute("UPDATE users SET banned_until = NULL WHERE id = %s", (user_id,))
            # No es necesario hacer commit aquí, se maneja en el administrador de contexto
            return True
    except Exception as e:
        logger.error(f"Error unbanning user: {e}", exc_info=True)
        return False    
