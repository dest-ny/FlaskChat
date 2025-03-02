# Archivo principal para iniciar la aplicación Flask
from app import socketio, app
from app.chat.models.db import db_start
import logging

logger = logging.getLogger(__name__)
startup_done = False

@app.before_request
def on_startup():
    """
    Función que se ejecuta antes de cada solicitud.
    Marca a todos los usuarios como desconectados
    al iniciar la aplicación.
    """
    global startup_done
    try:
        if not startup_done:
            db_start()
            startup_done = True
            logger.info("Todos los usuarios han sido marcados como desconectados.")
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        
if __name__ == '__main__':
    try:
        socketio.run(app, host="0.0.0.0")
    except Exception as e:
        logger.error(f"Error starting application: {e}", exc_info=True)

