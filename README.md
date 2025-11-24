# Sistema de reservas de salas de la UCU

Este repositorio contiene una aplicación web desarrollada en Flask para gestionar reservas de salas. Incluye autenticación con roles diferenciados (administrativo y usuarios finales), administración de reservas, generación de reportes y una interfaz web con plantillas y estilos propios.

## Estructura del proyecto
- **backend/**: aplicación Flask con rutas para autenticación, reservas y reportes, utilidades de validación y los modelos de acceso a datos.
- **frontend/**: archivos estáticos (CSS, JS, SCSS) y plantillas HTML utilizadas por Flask.
- **sql/**: scripts para crear la base de datos `ucu_reservas`, poblarla con datos de ejemplo, configurar triggers/eventos y asignar privilegios a los distintos usuarios de MySQL.
- **mysql/**: configuraciones adicionales de MySQL que se montan en el contenedor.
- **docker-compose.yml** y **dockerfile**: definen los servicios de la aplicación (Flask) y de la base de datos MySQL para un despliegue local con contenedores.

## Requisitos previos
- [Docker](https://www.docker.com/) y [Docker Compose](https://docs.docker.com/compose/) instalados.
- Opcional para ejecución sin contenedores: Python 3.11+ y un servidor MySQL accesible.

## Variables de entorno
Crea un archivo `.env` en la raíz del proyecto con las credenciales necesarias. Este archivo se comparte tanto con el contenedor de la aplicación como con el de la base de datos.

Variables utilizadas por los servicios de Docker:
- `MYSQL_ROOT_PASSWORD`: contraseña del usuario root de MySQL.
- `MYSQL_DATABASE`: nombre de la base de datos a crear (por defecto `ucu_reservas`).
- `MYSQL_USER` y `MYSQL_PASSWORD`: credenciales para el usuario adicional creado al iniciar el contenedor.
- `FLASK_ENV`: modo de ejecución de Flask (por ejemplo `development`).

Variables utilizadas por la aplicación Flask (se inyectan al contenedor `app` mediante `env_file`):
- `DB_HOST`: host de la base de datos (en Docker suele ser `db`).
- `DB_NAME`: nombre de la base de datos (por defecto `ucu_reservas`).
- `DB_USER_ADMINISTRATIVO` y `DB_PASS_ADMINISTRATIVO`: usuario y contraseña con permisos de administración de reservas.
- `DB_USER_REPORTE` y `DB_PASS_REPORTE`: usuario y contraseña con permisos de solo lectura para reportes.
- `DB_USER_LOGIN` y `DB_PASS_LOGIN`: usuario y contraseña para operaciones de autenticación y reservas de usuario final.
- `DB_SECRET_KEY`: clave secreta usada por Flask para sesiones y protección CSRF.

> Las contraseñas de los usuarios de MySQL se definen en los scripts de la carpeta `sql/`. Ajusta las variables de entorno para que coincidan con los valores configurados allí o actualiza los scripts según tu necesidad.

## Puesta en marcha con Docker
1. Asegúrate de que el archivo `.env` contenga todas las variables anteriores.
2. Construye e inicia los servicios con:
   ```bash
   docker compose up --build
   ```
3. La aplicación Flask quedará disponible en `http://localhost:5001` y el servidor MySQL en `localhost:3307` (mapeado al puerto 3306 interno del contenedor).

Al iniciar el contenedor de base de datos se ejecutan automáticamente los scripts de `sql/`, que crean la estructura, insertan datos de demostración, configuran triggers/eventos y asignan permisos a los usuarios.

## Ejecución local sin Docker
1. Crea y activa un entorno virtual.
2. Instala las dependencias del backend:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Exporta las variables de entorno indicadas en la sección anterior y asegúrate de tener un servidor MySQL accesible.
4. Ejecuta la aplicación:
   ```bash
   python backend/app.py
   ```
5. La aplicación quedará disponible en `http://localhost:5000`.

## Datos de referencia
- El puerto externo para la aplicación en Docker es `5001`, mientras que MySQL se expone en el puerto `3307`.
- Las rutas HTML y archivos estáticos se sirven desde la carpeta `frontend/`, configurada como `template_folder` y `static_folder` en `backend/app.py`.

## Resolución de problemas
- Verifica que las variables de entorno coincidan con los usuarios creados en los scripts de `sql/` si encuentras errores de autenticación contra la base de datos.
- Si necesitas reconstruir las imágenes tras modificar dependencias o scripts SQL, ejecuta `docker compose build --no-cache` seguido de `docker compose up`.
