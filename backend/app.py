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
@login_required
def home():
    conn = get_connection("login")
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            CASE 
                WHEN ppa.rol = 'Docente' THEN 'Docente'
                WHEN ppa.rol = 'Estudiante' AND pa.tipo = 'grado' THEN 'Estudiante de grado'
                WHEN ppa.rol = 'Estudiante' AND pa.tipo = 'posgrado' THEN 'Estudiante de posgrado'
                ELSE 'Desconocido'
            END AS tipo_persona
        FROM participantes_programa_academico ppa
        JOIN programas_academicos pa ON pa.nombre_programa = ppa.nombre_programa
        WHERE ppa.ci_participante = %s
        LIMIT 1;
    """, (current_user.ci,))

    tipo = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template(
        "home.html",
        usuario=current_user,
        tipo_persona=tipo["tipo_persona"] if tipo else "Desconocido"
    )

@app.route("/reservar", methods=["GET", "POST"])
@login_required
def reservar():
    # ============================================
    # Cargar datos para el formulario
    # ============================================
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT nombre_edificio FROM edificio;")
    edificios = cursor.fetchall()

    cursor.execute("SELECT nombre_sala, edificio FROM sala;")
    salas_raw = cursor.fetchall()
    salas_por_edificio = {}
    for s in salas_raw:
        salas_por_edificio.setdefault(s["edificio"], []).append(s["nombre_sala"])

    cursor.execute("SELECT id_turno, hora_inicio, hora_fin FROM turno;")
    turnos = cursor.fetchall()

    cursor.close()
    conn.close()

    # ============================================
    # Si se envió el formulario (POST)
    # ============================================
    if request.method == "POST":
        edificio = request.form["edificio"]
        nombre_sala = request.form["nombre_sala"]
        fecha = request.form["fecha"]
        id_turno = request.form["id_turno"]

        reserva = Reserva(
            id_reserva=None,
            nombre_sala=nombre_sala,
            edificio=edificio,
            fecha=fecha,
            id_turno=id_turno,
            estado="Activa"
        )

        conn = get_connection("login")  # conexión con permisos de escritura
        if conn:
            creada = modelReserva.crear_reserva(conn, reserva)
            conn.close()

            if creada:
                flash(f"Reserva creada correctamente para {fecha} en {edificio} - {nombre_sala}.", "success")
                return redirect(url_for("reservar"))  # 🔁 redirige con GET, evita reenvío del POST
            else:
                return redirect(url_for("reservar"))
        else:
            flash("No se pudo conectar a la base de datos.", "warning")

    # ============================================
    # Renderizar formulario
    # ============================================
    return render_template(
        "reservar.html",
        usuario=current_user,
        edificios=edificios,
        turnos=turnos,
        salas_por_edificio=salas_por_edificio
    )

@app.route("/misreservas", methods=["GET", "POST"])
@login_required
def mis_reservas():
    conn = get_connection("login")
    reservas = modelReserva.obtener_reservas_por_usuario(conn, current_user.ci)
    participantes = {}

    # Ver participantes / agregar participante
    if request.method == "POST":
        id_reserva = request.form.get("id_reserva")
        participantes[id_reserva] = modelReserva.obtener_participantes(conn, id_reserva)

    return render_template("misreservas.html", usuario=current_user, reservas=reservas, participantes=participantes)

@app.route("/cancelar_participacion/<int:id_reserva>", methods=["POST"])
@login_required
def cancelar_participacion(id_reserva):
    conn = get_connection("login")
    cursor = conn.cursor(dictionary=True)
    ci = current_user.ci  # o el campo que tengas para identificar al participante

    # Verificar que el participante pertenece a esa reserva
    cursor.execute("""
        SELECT * FROM reserva_participante
        WHERE ci_participante = %s AND id_reserva = %s;
    """, (ci, id_reserva))
    participacion = cursor.fetchone()

    if not participacion:
        flash("No estás asociado a esta reserva.", "error")
        conn.close()
        return redirect(url_for("mis_reservas"))

    # Marcar su participación como no confirmada
    cursor.execute("""
        UPDATE reserva_participante
        SET confirmado = FALSE
        WHERE ci_participante = %s AND id_reserva = %s;
    """, (ci, id_reserva))
    conn.commit()

    # Verificar si quedan participantes confirmados
    cursor.execute("""
        SELECT COUNT(*) AS restantes
        FROM reserva_participante
        WHERE id_reserva = %s AND confirmado = TRUE;
    """, (id_reserva,))
    restantes = cursor.fetchone()["restantes"]

    # Si no queda nadie confirmado, cancelar toda la reserva
    if restantes == 0:
        cursor.execute("""
            UPDATE reserva
            SET estado = 'cancelada'
            WHERE id_reserva = %s;
        """, (id_reserva,))
        conn.commit()
        flash("Se canceló toda la reserva porque no quedan participantes confirmados.", "warning")
    else:
        flash("Tu participación en la reserva fue cancelada.", "success")

    conn.close()
    return redirect(url_for("mis_reservas"))

@app.route("/sanciones", methods=["GET"])
@login_required
def sanciones():
    conn = get_connection("login")
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT fecha_inicio, fecha_fin
        FROM sancion_participante
        WHERE ci_participante = %s
        ORDER BY fecha_inicio DESC;
    """, (current_user.ci,))
    sanciones = cursor.fetchall()

    hoy = date.today()
    sanciones_ordenadas = []

    for s in sanciones:
        dias_restantes = (s["fecha_fin"] - hoy).days
        s["dias_restantes"] = max(dias_restantes, 0)
        s["estado"] = "Activa" if dias_restantes >= 0 else "Expirada"
        sanciones_ordenadas.append(s)

    # Orden: primero activas, luego expiradas
    sanciones_ordenadas.sort(key=lambda x: x["estado"] != "Activa")

    return render_template(
        "sanciones.html",
        usuario=current_user,
        sanciones=sanciones_ordenadas
    )

@app.route("/unirme", methods=["GET", "POST"])
@login_required
def unirme():
    conn = get_connection("login")
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        id_reserva = request.form.get("id_reserva")

        # Verificar que la reserva exista y esté activa
        cursor.execute("""
            SELECT r.id_reserva, r.fecha, r.id_turno, s.capacidad, s.tipo_sala,
                   (SELECT COUNT(*) FROM reserva_participante rp WHERE rp.id_reserva = r.id_reserva) AS ocupados
            FROM reserva r
            JOIN sala s ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
            WHERE r.id_reserva = %s AND r.estado = 'Activa';
        """, (id_reserva,))
        reserva = cursor.fetchone()

        if not reserva:
            flash("La reserva no existe o ya no está activa.", "error")

        else:
            # Verificar sanciones activas
            cursor.execute("""
                SELECT DATE_FORMAT(fecha_fin, '%d/%m/%Y') AS fin
                FROM sancion_participante
                WHERE ci_participante = %s
                AND CURDATE() BETWEEN fecha_inicio AND fecha_fin;
            """, (current_user.ci,))
            sancion = cursor.fetchone()

            if sancion:
                flash(f"No puedes unirte a la sala: estás sancionado hasta el {sancion['fin']}.", "error")
                cursor.close(); conn.close()
                return render_template("unirme.html", usuario=current_user)

            # Verificar tipo de sala vs tipo de usuario
            tipo_sala = reserva["tipo_sala"].lower()
            tipo_usuario = current_user.tipo.lower()

            if tipo_sala == "posgrado" and "grado" in tipo_usuario:
                flash("Solo posgrado o docentes pueden unirse a esta sala.", "error")
                cursor.close(); conn.close()
                return render_template("unirme.html", usuario=current_user)

            if tipo_sala == "docente" and "docente" not in tipo_usuario:
                flash("Solo docentes pueden unirse a esta sala.", "error")
                cursor.close(); conn.close()
                return render_template("unirme.html", usuario=current_user)

            # Verificar si ya está en la reserva
            cursor.execute("""
                SELECT 1 FROM reserva_participante
                WHERE ci_participante = %s AND id_reserva = %s;
            """, (current_user.ci, id_reserva))
            if cursor.fetchone():
                flash("Ya sos participante de esta reserva.", "warning")

            # Verificar capacidad
            elif reserva["ocupados"] >= reserva["capacidad"]:
                flash("La sala ya alcanzó su capacidad máxima.", "error")

            else:
                # Restricciones de grado: límite diario y semanal
                if "grado" in tipo_usuario:
                    # Límite diario: 2 horas por día
                    cursor.execute("""
                        SELECT COUNT(*) AS bloques
                        FROM reserva_participante rp
                        JOIN reserva r ON rp.id_reserva = r.id_reserva
                        WHERE rp.ci_participante = %s AND r.fecha = %s AND r.estado = 'Activa';
                    """, (current_user.ci, reserva["fecha"]))
                    if cursor.fetchone()["bloques"] >= 2:
                        flash("No podés tener más de 2 horas de reserva por día.", "error")
                        cursor.close(); conn.close()
                        return render_template("unirme.html", usuario=current_user)

                    # Límite semanal: 3 reservas activas
                    hoy = date.today()
                    inicio_semana = hoy - timedelta(days=hoy.weekday())  # lunes
                    fin_semana = inicio_semana + timedelta(days=6)       # domingo

                    cursor.execute("""
                        SELECT COUNT(*) AS cantidad
                        FROM reserva_participante rp
                        JOIN reserva r ON rp.id_reserva = r.id_reserva
                        WHERE rp.ci_participante = %s
                          AND r.fecha BETWEEN %s AND %s
                          AND r.estado = 'Activa';
                    """, (current_user.ci, inicio_semana, fin_semana))
                    if cursor.fetchone()["cantidad"] >= 3:
                        flash("No podés tener más de 3 reservas activas esta semana.", "error")
                        cursor.close(); conn.close()
                        return render_template("unirme.html", usuario=current_user)

                # Si pasa todas las validaciones, se une
                cursor.execute("""
                    INSERT INTO reserva_participante (ci_participante, id_reserva, fecha_solicitud_reserva)
                    VALUES (%s, %s, CURDATE());
                """, (current_user.ci, id_reserva))
                conn.commit()
                flash("Te uniste correctamente a la sala.", "success")

    cursor.close()
    conn.close()
    return render_template("unirme.html", usuario=current_user)



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

