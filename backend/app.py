from flask import Flask, request, render_template, redirect, url_for, flash
from database import get_connection
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from models.modelUser import modelUser
from models.entities.user import User
from models.entities.reserva import Reserva
from models.modelReserva import modelReserva
import os
from dotenv import load_dotenv
from datetime import date


# Cargar las variables del archivo .env
load_dotenv()


# ==================================================
# CONFIGURACIÓN BASE
# ==================================================
app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend")
csrf = CSRFProtect(app)  # Protección CSRF para formularios
app.secret_key = os.getenv("DB_SECRET_KEY")  # Necesario para sesiones y flash()


# Inicializar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Si no hay sesión, redirige acá
login_manager.login_message = "Por favor inicie sesión para acceder a esta página."
login_manager.login_message_category = "warning"  # ⚠️ Amarillo




# ==================================================
# FUNCIÓN PARA CARGAR USUARIO POR ID
# ==================================================
@login_manager.user_loader
def load_user(user_id):
   """Flask-Login usa esta función para mantener la sesión."""
   conn = get_connection("login")
   user_data = modelUser.get_by_id(conn, user_id)
   return user_data  # Debe devolver un objeto User o None

# ==================================================
# RUTAS
# ==================================================
@app.route("/")
def index():
   return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "POST":
      user = User(0, request.form["email"], request.form["password"], "", "", "")
      conn = get_connection("login")  # crear conexión por request
      logged_user = modelUser.login(conn, user)

      if logged_user is not None:
          if logged_user.password:  # contraseña y usuario correcta
              login_user(logged_user)
              return redirect(url_for("home"))
      else:
          conn2 = get_connection("reportes")
          cursor = conn2.cursor(dictionary=True)
          cursor.execute("SELECT email FROM login WHERE email= %s LIMIT 1", (request.form["email"],)) #busca si existe el usuario
          existe = cursor.fetchone()
          cursor.close()
          conn2.close()

          if existe:
             flash("Contraseña incorrecta", "error")
          else:
             flash("Usuario no encontrado", "error")
          return render_template("login.html")

      return render_template("login.html")
  else:
    return render_template("login.html")



@app.route("/home")
@login_required  # protege la ruta
def home():
   return render_template("home.html", usuario=current_user)

@app.route("/reservar", methods=["GET", "POST"])
@login_required
def reservar():
    edificios = []
    turnos = []
    salas_por_edificio = {}

    conn = get_connection()
    if conn is not None:
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)

            # Obtener edificios
            cursor.execute("SELECT nombre_edificio FROM edificio;")
            edificios = cursor.fetchall()

            # Obtener salas agrupadas por edificio
            cursor.execute("SELECT nombre_sala, edificio FROM sala;")
            salas_raw = cursor.fetchall()
            for sala in salas_raw:
                salas_por_edificio.setdefault(sala["edificio"], []).append(sala["nombre_sala"])

            # Obtener turnos
            cursor.execute("SELECT id_turno, hora_inicio, hora_fin FROM turno;")
            turnos = cursor.fetchall()
        finally:
            if cursor is not None:
                cursor.close()
            conn.close()
    else:
        flash("⚠️ No se pudieron cargar los datos de reserva.", "error")

    # Si se hace POST (crear reserva)
    if request.method == "POST":
        edificio = request.form["edificio"]
        nombre_sala = request.form["nombre_sala"]
        fecha_str = request.form["fecha"]
        id_turno = request.form["id_turno"]

        try:
            fecha_reserva = date.fromisoformat(fecha_str)
        except ValueError:
            flash("❌ La fecha proporcionada no es válida.", "error")
        else:
            if fecha_reserva < date.today():
                flash("❌ No se puede reservar una fecha pasada.", "error")
            else:
                reserva = Reserva(
                    id_reserva=None,
                    nombre_sala=nombre_sala,
                    edificio=edificio,
                    fecha=fecha_reserva,
                    id_turno=int(id_turno)
                )

                conn_admin = get_connection("administrativo")
                if conn_admin is None:
                    flash("⚠️ No se pudo establecer la conexión para crear la reserva.", "error")
                else:
                    try:
                        modelReserva.crear_reserva(conn_admin, reserva)
                    finally:
                        conn_admin.close()

    return render_template(
        "reservar.html",
        usuario=current_user,
        edificios=edificios,
        turnos=turnos,
        salas_por_edificio=salas_por_edificio
    )

@app.route("/misreservas", methods=["GET"])
@login_required
def mis_reservas():
    conn = get_connection("login")
    reservas = modelReserva.obtener_reservas_por_usuario(conn, current_user.ci)
    return render_template("misreservas.html", usuario=current_user, reservas=reservas)

@app.route("/sanciones", methods=["GET"])
@login_required  # protege la ruta
def sanciones():
   return render_template("sanciones.html", usuario=current_user)


@app.route("/logout")
@login_required
def logout():
   logout_user()
   flash("Sesión cerrada correctamente.", "success")
   return redirect(url_for("login"))


@app.after_request
def set_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    # permitir JS local y tokens de Flask
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response


# ==================================================
# MAIN
# ==================================================
if __name__ == "__main__":
    csrf.init_app(app)
    app.run(debug=True)

