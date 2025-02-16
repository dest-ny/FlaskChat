from app import socketio, app
from app.chat.models.db import db_start

startup_done = False

@app.before_request
def on_startup():
    global startup_done
    if not startup_done:
        db_start()
        startup_done = True
        print("Todos los usuarios han sido marcados como desconectados.")
        
if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0")

