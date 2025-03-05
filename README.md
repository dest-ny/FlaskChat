# FlaskChat

Una aplicación de chat en tiempo real construida con Flask, Socket.IO y MySQL. FlaskChat permite a los usuarios comunicarse instantáneamente, con características avanzadas de autenticación, gestión de mensajes y capacidades de moderación.


## Características

- **Comunicación en Tiempo Real**: Mensajería instantánea utilizando Socket.IO para una experiencia fluida sin necesidad de recargar la página.
- **Sistema de Autenticación**: Sistema seguro de inicio de sesión y registro con contraseñas cifradas mediante Bcrypt.
- **Roles de Usuario**: Diferentes niveles de permisos (usuarios regulares, moderadores, administradores) para una gestión eficiente de la comunidad.
- **Herramientas de Moderación**: Funcionalidad de timeout y baneo para moderadores.
- **Gestión de Mensajes**: Carga del historial de mensajes con paginación.
- **Barra de Administración**: Estadísticas del sistema y gestión de usuarios para administradores, con información detallada sobre el rendimiento y uso.
- **Interfaz Intuitiva**: Diseño limpio y fácil de usar.
- **Información en Tiempo Real**: Los usuarios reciben actualizaciones instantáneas sobre nuevos mensajes y cambios en el estado de otros usuarios.

## Tecnologías

- **Backend**: 
  - Flask (Python): Framework web ligero y flexible para el desarrollo rápido de aplicaciones.
  - Flask-SocketIO: Extensión para integrar Socket.IO con Flask, facilitando la comunicación bidireccional en tiempo real.
  - Flask-MySQL: Conector para interactuar con bases de datos MySQL desde aplicaciones Flask.
  - Flask-Bcrypt: Extensión para el cifrado seguro de contraseñas.

- **Base de Datos**: 
  - MySQL: Sistema de gestión de bases de datos relacional para almacenar usuarios y mensajes.

- **Seguridad**: 
  - Bcrypt: Algoritmo de hashing para el almacenamiento seguro de contraseñas.
  - Validación de formularios: Protección contra inyección SQL y ataques XSS.

- **Frontend**: 
  - HTML5: Estructura semántica para el contenido web.
  - CSS3: Estilos modernos con flexbox para diseños responsivos.
  - JavaScript: Interactividad del lado del cliente y comunicación con Socket.IO.

## Instalación

### Requisitos Previos

- Python 3.8 o superior
- Servidor MySQL
- Git

### Configuración

1. **Clonar el repositorio**

```bash
git clone https://github.com/tuusuario/flaskchat.git
cd flaskchat
```

2. **Crear un entorno virtual**

```bash
python -m venv venv
```

3. **Activar el entorno virtual**

En Windows:
```bash
venv\Scripts\activate
```

En macOS/Linux:
```bash
source venv/bin/activate
```

4. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

5. **Configurar la base de datos**

Crear una base de datos MySQL y un usuario:

```sql
CREATE DATABASE flaskchat;
CREATE USER 'flaskchat'@'localhost' IDENTIFIED BY 'flaskchat';
GRANT ALL PRIVILEGES ON flaskchat.* TO 'flaskchat'@'localhost';
FLUSH PRIVILEGES;
```

Importar el esquema de la base de datos:

```bash
mysql -u flaskchat -p flaskchat < flaskchat.sql
```

6. **Configurar la aplicación**

Actualizar la configuración de conexión a la base de datos en `app/__init__.py` si es necesario:

```python
app.config['MYSQL_DATABASE_HOST'] = "localhost"  # Cambiar a tu host MySQL
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_USER'] = "flaskchat"
app.config['MYSQL_DATABASE_PASSWORD'] = "flaskchat"
app.config['MYSQL_DATABASE_DB'] = "flaskchat"
```

7. **Ejecutar la aplicación**

```bash
python run.py
```

La aplicación estará disponible en `http://localhost:5000`

## Estructura del Proyecto

```
flaskchat/
├── app/                    # Paquete principal de la aplicación
│   ├── __init__.py         # Inicialización de la aplicación
│   ├── chat/               # Módulo de chat
│   │   ├── controllers/    # Controladores de rutas y eventos
│   │   │   ├── __init__.py # Inicialización del Blueprint
│   │   │   ├── events.py   # Manejadores de eventos Socket.IO
│   │   │   └── routes.py   # Manejadores de rutas HTTP
│   │   └── models/         # Modelos de base de datos
│   │       └── db.py       # Funciones de interacción con la base de datos
│   ├── static/             # Recursos estáticos
│   │   ├── css/            # Hojas de estilo CSS
│   │   │   └── styles.css  # Hoja de estilo principal
│   │   └── javascript/     # Archivos JavaScript
│   │       ├── chatjs.js   # Funcionalidad del chat
│   │       └── devbar.js   # Funcionalidad del panel de administración
│   └── templates/          # Plantillas HTML
│       ├── base.html       # Plantilla base
│       ├── index.html      # Interfaz principal del chat
│       ├── login.html      # Página de inicio de sesión
│       └── register.html   # Página de registro
├── flaskchat.sql           # Esquema de la base de datos
├── requirements.txt        # Dependencias de Python
├── run.py                  # Punto de entrada de la aplicación
└── README.md               # Este archivo
```

## Descripción Detallada de los Componentes

### Módulo de Chat (`app/chat`)

El núcleo de la aplicación, donde se organizan todos los recursos necesarios para su funcionalidad, como controladores (rutas y eventos) y modelos (lógica de negocio con la base de datos).

### Controladores (`app/chat/controllers`)

#### Eventos (`events.py`)

Controla los eventos de Socket.IO para la comunicación en tiempo real en el chat:

- **conectado()**: Se ejecuta al conectarse un usuario para comprobar si está baneado; si lo está, lo desconecta. Además, marca al usuario como en línea en la base de datos y notifica a los demás usuarios.
- **desconectado()**: Se ejecuta cuando un usuario se desconecta para marcarlo como desconectado en la base de datos y notifica a los demás usuarios (si no está baneado).
- **recibir_mensaje(msg)**: Se ejecuta cuando un usuario manda un mensaje en el chat para guardarlo en la base de datos y mandarlo a todos los usuarios conectados.
- **timeout_user(data)**: Permite a un moderador (rol >= 5) que banee temporalmente o permanentemente a un usuario de menor rango. Guarda la "sanción" en la base de datos, desconecta al usuario afectado y notifica a los demás usuarios.
- **clear_messages()**: Solo lo ejecutan administradores (rol >= 10). Permite borrar todos los mensajes del chat en la base de datos, notificando a los usuarios para limpiar sus chats.

#### Rutas (`routes.py`)

Contiene las rutas principales de la aplicación:

- **/ chat**: Muestra la interfaz de chat si el usuario ha iniciado sesión y no está baneado. Si el usuario está baneado, lo redirige al login con un mensaje de expulsión.
- **/load_messages**: Carga mensajes del chat con paginación (offset en la URL). Restringe el acceso a usuarios no autenticados o baneados.
- **/get_info**: Devuelve estadísticas del sistema (uso de CPU, memoria, etc.). Solo accesible para administradores (role >= 10).
- **/login**: Procesa el formulario de inicio de sesión. Si el usuario ya está autenticado, lo redirige al chat. Aplica validaciones y verifica si el usuario está baneado.
- **/logout**: Cierra la sesión del usuario y lo redirige al login.
- **/register**: Maneja el registro de nuevos usuarios con validaciones de nombre y contraseña.
- **/search_users**: Permite a administradores buscar usuarios por nombre.
- **/change_role**: Permite a administradores cambiar el rol de un usuario.
- **/unban_user**: Permite a administradores desbanear usuarios.

### Modelos (`app/chat/models`)

#### Base de Datos (`db.py`)

Módulo que permite manejar la interacción con la base de datos MySQL:

- **Conexión**: Gestión segura de la conexión con la base de datos mediante el uso de un contextmanager.

### Plantillas (`app/templates`)

- **base.html**: Plantilla base para login.html y register.html. Define la cabecera, pie de página, formulario, manejo de errores y mensajes flash.
- **index.html**: Define la vista principal del chat, mostrando el nombre de usuario logueado, formulario para enviar mensajes, área de mensajes y lista de usuarios conectados.
- **login.html**: Página de inicio de sesión que hereda de base.html.
- **register.html**: Página de registro que hereda de base.html.

### Recursos Estáticos (`app/static`)

- **CSS (styles.css)**: Define el estilo de la interfaz de usuario, enfocándose en la presentación visual, usabilidad e interactividad.
- **JavaScript**:
  - **chatjs.js**: Gestiona el funcionamiento del chat en tiempo real usando Socket.IO para la comunicación entre el cliente y el servidor.
  - **devbar.js**: Gestiona la barra de desarrolladores activa en el chat.

## Roles de Usuario

FlaskChat implementa un sistema de permisos basado en roles:

- **Usuarios Regulares (rol 0-4)**: 
  - Pueden enviar y recibir mensajes
  - Ver la lista de usuarios conectados
  - Acceder al historial de mensajes

- **Moderadores (rol 5-9)**: 
  - Todas las capacidades de los usuarios regulares
  - Pueden aplicar timeout a usuarios (baneo temporal)
  - Pueden banear permanentemente a usuarios de menor rango
  - Ver información básica sobre los usuarios

- **Administradores (rol 10+)**: 
  - Todas las capacidades de los moderadores
  - Pueden borrar todos los mensajes del chat
  - Pueden cambiar el rol de cualquier usuario
  - Pueden desbanear usuarios
  - Acceso a estadísticas del sistema (CPU, memoria, etc.)
  - Búsqueda avanzada de usuarios

## Endpoints de la API

### Autenticación

- `GET /login` - Muestra el formulario de inicio de sesión
- `POST /login` - Procesa el inicio de sesión
- `GET /register` - Muestra el formulario de registro
- `POST /register` - Procesa el registro
- `GET /logout` - Cierra la sesión del usuario

### Chat

- `GET /` - Interfaz principal del chat
- `GET /load_messages` - Carga el historial de mensajes del chat con paginación

### Administración

- `GET /get_info` - Obtiene estadísticas del sistema (solo administradores)
- `GET /search_users` - Busca usuarios por nombre (solo administradores)
- `POST /change_role` - Cambia el rol de un usuario (solo administradores)
- `POST /unban_user` - Desbanea a un usuario (solo administradores)

## Eventos de Socket.IO

### Cliente a Servidor

- `mensaje` - Envía un mensaje al chat
- `timeout_user` - Aplica timeout a un usuario (moderadores+)
- `clear_messages` - Borra todos los mensajes del chat (solo administradores)

### Servidor a Cliente

- `mensaje` - Recibe un mensaje de otro usuario
- `usuarios_online` - Actualiza la lista de usuarios conectados
- `force_disconnect` - Fuerza la desconexión del cliente (cuando es baneado)
- `clear_messages` - Limpia la visualización del chat

## Seguridad

FlaskChat implementa varias medidas de seguridad:

- **Cifrado de Contraseñas**: Utiliza Bcrypt para almacenar contraseñas de forma segura.
- **Protección de Sesiones**: Utiliza cookies seguras y tokens de sesión.
- **Validación de Entradas**: Sanitiza todas las entradas de usuario para prevenir inyecciones SQL y ataques XSS.
- **Control de Acceso**: Verifica los permisos de usuario antes de permitir acciones restringidas.

## Escalabilidad

La aplicación está diseñada para ser escalable:

- **Arquitectura Modular**: Uso de Blueprints de Flask para organizar el código.
- **Separación de Responsabilidades**: Sigue el patrón MVC (Modelo-Vista-Controlador).
- **Conexiones Eficientes**: Gestión adecuada de conexiones a la base de datos.
- **Paginación**: Implementada para manejar grandes volúmenes de mensajes.

## Contribuir

1. Haz un fork del repositorio
2. Crea una rama para tu funcionalidad: `git checkout -b nombre-funcionalidad`
3. Haz commit de tus cambios: `git commit -m 'Añadir alguna funcionalidad'`
4. Haz push a la rama: `git push origin nombre-funcionalidad`
5. Envía un pull request

## Solución de Problemas

### Problemas Comunes

1. **Error de conexión a la base de datos**:
   - Verifica que el servidor MySQL esté en ejecución
   - Comprueba las credenciales en `app/__init__.py`
   - Asegúrate de que la base de datos `flaskchat` exista

2. **Socket.IO no se conecta**:
   - Verifica que no haya bloqueadores de scripts en tu navegador
   - Comprueba la consola del navegador para errores
   - Asegúrate de que el puerto no esté bloqueado por un firewall

3. **Problemas de registro/inicio de sesión**:
   - Limpia las cookies del navegador
   - Verifica los requisitos de contraseña
   - Comprueba los logs del servidor para errores específicos

## Planes Futuros

- Aprobar.

## Agradecimientos
- Boa, por enseñarnos Python.

---

Desarrollado con ❤️ por Georgi y Daniel
