from flask import Flask, request, render_template, redirect, url_for, flash
from database import get_connection
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from models.modelUser import modelUser
from models.entities.user import User
from models.entities.reserva import Reserva
from models.modelReserva import modelReserva
import os
import re
from dotenv import load_dotenv
from datetime import datetime, date, time, timedelta
from werkzeug.security import generate_password_hash

from utilidades import (
    generar_contrasena,
    validar_cedula_uruguaya,
    validar_email_institucional,
    normalizar_nombre,
    normalizar_sala,
    crear_notificacion
)
from reportes import reportes_bp

from hash_existing_passwords import hash_existing_passwords

# Cargar las variables del archivo .env
load_dotenv()


# ==================================================
# CONFIGURACIÓN BASE
# ==================================================
app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend")
app.secret_key = os.getenv("DB_SECRET_KEY")  # Necesario para sesiones y flash()

# CSRF (solo una vez)
csrf = CSRFProtect()
csrf.init_app(app)


# Inicializar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Si no hay sesión, redirige acá
login_manager.login_message = "Por favor inicie sesión para acceder a esta página."
login_manager.login_message_category = "warning"  # ⚠️ Amarillo


# =================================================
# REGISTRAR BLUEPRINTS
# =================================================
app.register_blueprint(reportes_bp)

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
        conn = get_connection("login")
        logged_user = modelUser.login(conn, user)

        if logged_user is not None:
            if logged_user.password:  # contraseña correcta
                login_user(logged_user)

                # Verificar si es el administrador
                if logged_user.email == "administrativo@ucu.edu.uy":
                    return redirect(url_for("admin"))
                else:
                    return redirect(url_for("home"))

        # Si no se pudo loguear correctamente
        conn2 = get_connection("reportes")
        cursor = conn2.cursor(dictionary=True)
        cursor.execute("SELECT email FROM login WHERE email = %s LIMIT 1", (request.form["email"],))
        existe = cursor.fetchone()
        cursor.close()
        conn2.close()

        if existe:
            flash("Contraseña incorrecta", "error")
        else:
            flash("Usuario no encontrado", "error")

        return render_template("login.html")

    # Si entra por GET
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
                ELSE 'Administrativo'
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
        tipo_persona=tipo["tipo_persona"] if tipo else "Perfil administrador"
    )

@app.route("/reservar", methods=["GET", "POST"])
@login_required
def reservar():
    # ============================================
    # Cargar datos para el formulario
    # ============================================
    conn = get_connection("login")
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
    conn = get_connection("administrativo")
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

        # Notificar a los que estaban
        crear_notificacion(cursor, ci, f"Tu reserva #{id_reserva} fue cancelada por falta de participantes.")
        conn.commit()

        flash("Se canceló toda la reserva porque no quedan participantes confirmados.", "warning")
    else:
        flash("Tu participación en la reserva fue cancelada.", "success")
        crear_notificacion(cursor, ci, f"Cancelaste tu participación en la reserva #{id_reserva}.")
        conn.commit()

    conn.close()
    return redirect(url_for("mis_reservas"))

@app.route("/sanciones", methods=["GET"])
@login_required
def sanciones():
    conn = get_connection("login")
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT fecha_inicio, fecha_fin, activa
        FROM sancion_participante
        WHERE ci_participante = %s
        ORDER BY fecha_inicio DESC;
    """, (current_user.ci,))
    sanciones = cursor.fetchall()

    hoy = date.today()
    sanciones_ordenadas = []

    for s in sanciones:
        dias_restantes = (s["fecha_fin"] - hoy).days

        # Si está activa y faltan días → mostrar días
        if s["activa"] == 1 and dias_restantes >= 0:
            s["estado"] = "Activa"
            s["dias_restantes"] = dias_restantes
        else:
            s["estado"] = "Expirada"
            s["dias_restantes"] = "-"

        sanciones_ordenadas.append(s)

    # Orden: primero activas
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
                   (SELECT COUNT(*) FROM reserva_participante rp WHERE rp.id_reserva = r.id_reserva AND rp.confirmado = TRUE) AS ocupados
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
                AND CURDATE() BETWEEN fecha_inicio AND fecha_fin
                AND activa = 1;
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

            # Verificar si ya existe una fila en reserva_participante
            cursor.execute("""
                SELECT confirmado
                FROM reserva_participante
                WHERE ci_participante = %s AND id_reserva = %s;
            """, (current_user.ci, id_reserva))

            row = cursor.fetchone()

            # Caso 1: ya está confirmado → bloquear
            if row and row["confirmado"] == 1:
                flash("Ya sos participante de esta reserva.", "warning")
                cursor.close(); conn.close()
                return render_template("unirme.html", usuario=current_user)

            # Verificar capacidad antes de continuar
            if reserva["ocupados"] >= reserva["capacidad"]:
                flash("La sala ya alcanzó su capacidad máxima.", "error")
                cursor.close(); conn.close()
                return render_template("unirme.html", usuario=current_user)

            # Restricciones de grado: límite diario y semanal
            if "grado" in tipo_usuario:
                # Límite diario: 2 horas por día
                cursor.execute("""
                    SELECT COUNT(*) AS bloques
                    FROM reserva_participante rp
                    JOIN reserva r ON rp.id_reserva = r.id_reserva
                    WHERE rp.ci_participante = %s AND r.fecha = %s AND r.estado = 'Activa' AND rp.confirmado = TRUE;
                """, (current_user.ci, reserva["fecha"]))
                if cursor.fetchone()["bloques"] >= 2:
                    flash("No podés tener más de 2 horas de reserva por día.", "error")
                    cursor.close(); conn.close()
                    return render_template("unirme.html", usuario=current_user)

                # Límite semanal: 3 reservas activas
                hoy = date.today()
                inicio_semana = hoy - timedelta(days=hoy.weekday())
                fin_semana = inicio_semana + timedelta(days=6)

                cursor.execute("""
                    SELECT COUNT(*) AS cantidad
                    FROM reserva_participante rp
                    JOIN reserva r ON rp.id_reserva = r.id_reserva
                    WHERE rp.ci_participante = %s
                      AND r.fecha BETWEEN %s AND %s
                      AND r.estado = 'Activa'
                      AND rp.confirmado = TRUE;
                """, (current_user.ci, inicio_semana, fin_semana))
                if cursor.fetchone()["cantidad"] >= 3:
                    flash("No podés tener más de 3 reservas activas esta semana.", "error")
                    cursor.close(); conn.close()
                    return render_template("unirme.html", usuario=current_user)

            # Caso 2: la fila existe pero estaba desconfirmado → reactivar
            if row and row["confirmado"] == 0:
                cursor.execute("""
                    UPDATE reserva_participante
                    SET confirmado = TRUE
                    WHERE ci_participante = %s AND id_reserva = %s;
                """, (current_user.ci, id_reserva))
                conn.commit()
                flash("Te uniste nuevamente a la sala.", "success")
                cursor.close(); conn.close()
                return render_template("unirme.html", usuario=current_user)

            # Caso 3: no existía → insertar nuevo registro
            cursor.execute("""
                INSERT INTO reserva_participante (ci_participante, id_reserva, fecha_solicitud_reserva, confirmado)
                VALUES (%s, %s, CURDATE(), TRUE);
            """, (current_user.ci, id_reserva))
            conn.commit()
            flash("Te uniste correctamente a la sala.", "success")

    cursor.close()
    conn.close()
    return render_template("unirme.html", usuario=current_user)


@app.route("/notificaciones")
@login_required
def notificaciones():
    conn = get_connection("login")
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id_notificacion, mensaje, fecha, leida
        FROM notificacion
        WHERE ci_participante = %s
        ORDER BY fecha DESC;
    """, (current_user.ci,))

    notificaciones = cursor.fetchall()

    # marcar como leídas
    cursor.execute("""
        UPDATE notificacion
        SET leida = TRUE
        WHERE ci_participante = %s;
    """, (current_user.ci,))

    conn.commit()
    return render_template("notificaciones.html", notificaciones=notificaciones)

# ==================================================
# RUTAS PANEL ADMINISTRADOR
# ==================================================

@app.route("/admin")
@login_required
def admin():
    # Solo el admin puede acceder
    if current_user.email != "administrativo@ucu.edu.uy":
        return redirect(url_for("home"))

    return render_template("home-admin.html", usuario=current_user)


@app.route("/admin/participantes", methods=["GET", "POST"])
@login_required
def abm_participantes():
    # Solo el admin puede acceder
    if current_user.email != "administrativo@ucu.edu.uy":
        return redirect(url_for("home"))

    conn = get_connection("administrativo")
    cursor = conn.cursor(dictionary=True)

    # ============================================
    # Obtener facultades y programas
    # ============================================
    cursor.execute("SELECT id_facultad, nombre FROM facultad ORDER BY nombre;")
    facultades = cursor.fetchall()

    cursor.execute("""
        SELECT pa.nombre_programa, f.nombre AS facultad
        FROM programas_academicos pa
        JOIN facultad f ON pa.id_facultad = f.id_facultad
        ORDER BY f.nombre, pa.nombre_programa;
    """)
    rows = cursor.fetchall()

    programas_por_facultad = {}
    for row in rows:
        fac = row["facultad"]
        programas_por_facultad.setdefault(fac, []).append(row["nombre_programa"])

    # ============================================
    # Manejo de formulario (alta / baja / edición)
    # ============================================
    if request.method == "POST":
        accion = request.form.get("accion")

        # ============================================
        # AGREGAR PARTICIPANTE
        # ============================================
        if accion == "agregar":
            ci = request.form.get("ci")
            nombre = request.form.get("nombre")
            apellido = request.form.get("apellido")
            email = request.form.get("email")
            facultad = request.form.get("facultad")
            programa = request.form.get("programa")
            rol = request.form.get("rol")

            # VALIDAR NOMBRE Y APELLIDO (caracteres permitidos)
            NOMBRE_REGEX = r"^[A-Za-zÀ-ÿ' ]+$"

            if not re.match(NOMBRE_REGEX, nombre):
                flash("El nombre contiene caracteres inválidos. Solo se permiten letras, espacios y apóstrofes.", "error")
                return redirect(url_for("abm_participantes"))

            if not re.match(NOMBRE_REGEX, apellido):
                flash("El apellido contiene caracteres inválidos. Solo se permiten letras, espacios y apóstrofes.", "error")
                return redirect(url_for("abm_participantes"))

            # NORMALIZAR NOMBRE Y APELLIDO
            nombre = normalizar_nombre(nombre)
            apellido = normalizar_nombre(apellido)

            # Validaciones

            MAX_LEN = 50  # límite en la definición de la tabla en la bd

            # validar cantidad de caracteres
            if len(nombre) > MAX_LEN:
                flash(f"El nombre no puede superar {MAX_LEN} caracteres.", "error")
                return redirect(url_for("abm_participantes"))

            if len(apellido) > MAX_LEN:
                flash(f"El apellido no puede superar {MAX_LEN} caracteres.", "error")
                return redirect(url_for("abm_participantes"))
            
            # validar cédula y email
            
            if not validar_cedula_uruguaya(ci):
                flash("Cédula inválida. Debe ser una cédula uruguaya válida.", "error")
                return redirect(url_for("abm_participantes"))

            if not validar_email_institucional(email, rol):
                dominio = "@correo.ucu.edu.uy" if rol.lower() == "estudiante" else "@ucu.edu.uy"
                flash(f"Email institucional inválido. Debe terminar en {dominio}", "error")
                return redirect(url_for("abm_participantes"))

            try:
                cursor.execute("SELECT 1 FROM participantes WHERE ci = %s OR email = %s", (ci, email))
                if cursor.fetchone():
                    flash("Ya existe un participante con ese CI o email.", "error")
                else:
                    # Insertar participante
                    cursor.execute("""
                        INSERT INTO participantes (ci, nombre, apellido, email)
                        VALUES (%s, %s, %s, %s)
                    """, (ci, nombre, apellido, email))

                    # Generar y guardar contraseña
                    contrasena_generada = generar_contrasena(10)
                    contrasena_hash = generate_password_hash(contrasena_generada)

                    cursor.execute("""
                        INSERT INTO login (email, password)
                        VALUES (%s, %s)
                    """, (email, contrasena_hash))

                    # Asociar a programa
                    cursor.execute("""
                        INSERT INTO participantes_programa_academico (ci_participante, nombre_programa, rol)
                        VALUES (%s, %s, %s)
                    """, (ci, programa, rol))

                    conn.commit()

                    flash(
                        f"{nombre} {apellido} fue agregado correctamente a {programa} ({rol}). "
                        f"Contraseña generada: {contrasena_generada}",
                        "success"
                    )

            except Exception as e:
                conn.rollback()
                flash(f"Error al agregar participante: {e}", "error")

            return redirect(url_for("abm_participantes"))

        # ============================================
        # EDITAR PARTICIPANTE
        # ============================================
        elif accion == "editar":
            ci = request.form.get("ci")
            nombre = request.form.get("nombre")
            apellido = request.form.get("apellido")
            email = request.form.get("email")
            programa = request.form.get("programa")
            rol = request.form.get("rol")

            # VALIDAR NOMBRE Y APELLIDO (caracteres permitidos)
            NOMBRE_REGEX = r"^[A-Za-zÀ-ÿ' ]+$"

            if not re.match(NOMBRE_REGEX, nombre):
                flash("El nombre contiene caracteres inválidos. Solo se permiten letras, espacios y apóstrofes.", "error")
                return redirect(url_for("abm_participantes"))

            if not re.match(NOMBRE_REGEX, apellido):
                flash("El apellido contiene caracteres inválidos. Solo se permiten letras, espacios y apóstrofes.", "error")
                return redirect(url_for("abm_participantes"))

            # NORMALIZAR NOMBRE Y APELLIDO
            nombre = normalizar_nombre(nombre)
            apellido = normalizar_nombre(apellido)

            # Validaciones

            MAX_LEN = 50  # límite en la definición de la tabla en la bd

            # validar cantidad de caracteres
            if len(nombre) > MAX_LEN:
                flash(f"El nombre no puede superar {MAX_LEN} caracteres.", "error")
                return redirect(url_for("abm_participantes"))

            if len(apellido) > MAX_LEN:
                flash(f"El apellido no puede superar {MAX_LEN} caracteres.", "error")
                return redirect(url_for("abm_participantes"))
            
            # validar email


            if not validar_email_institucional(email, rol):
                dominio = "@correo.ucu.edu.uy" if rol.lower() == "estudiante" else "@ucu.edu.uy"
                flash(f"No se pudo modificar el participante. Email institucional inválido. Debe terminar en {dominio}", "error")
                return redirect(url_for("abm_participantes"))



            # No permitir tocar al admin
            if email == "administrativo@ucu.edu.uy":
                flash("No se puede modificar al usuario administrativo.", "warning")
                return redirect(url_for("abm_participantes"))

            try:
                # Update de datos básicos
                cursor.execute("""
                    UPDATE participantes
                    SET nombre = %s, apellido = %s, email = %s
                    WHERE ci = %s
                """, (nombre, apellido, email, ci))

                # Update de programa + rol
                cursor.execute("""
                    UPDATE participantes_programa_academico
                    SET nombre_programa = %s,
                        rol = %s
                    WHERE ci_participante = %s
                """, (programa, rol, ci))

                conn.commit()
                flash(f"{nombre} {apellido} actualizado correctamente.", "success")

            except Exception as e:
                conn.rollback()
                flash(f"Error al editar participante: {e}", "error")

            return redirect(url_for("abm_participantes"))


        # ============================================
        # ELIMINAR PARTICIPANTE
        # ============================================
        elif accion == "eliminar":
            ci = request.form.get("ci")

            cursor.execute("SELECT email FROM participantes WHERE ci = %s", (ci,))
            participante = cursor.fetchone()

            if not participante:
                flash("Participante no encontrado.", "error")
                return redirect(url_for("abm_participantes"))

            if participante["email"] == "administrativo@ucu.edu.uy":
                flash("No se puede eliminar al usuario administrativo.", "warning")
                return redirect(url_for("abm_participantes"))

            try:
                # Anular sanciones activas
                cursor.execute("""
                    UPDATE sancion_participante
                    SET activa = FALSE
                    WHERE ci_participante = %s
                    AND activa = TRUE;
                """, (ci,))

                # Anular asistencia y confirmación en reservas
                cursor.execute("""
                    UPDATE reserva_participante
                    SET asistencia = FALSE,
                        confirmado = FALSE
                    WHERE ci_participante = %s;
                """, (ci,))

                # Eliminar participante
                # se eliminan en cascada en los participantes_programa_academico y el login
                cursor.execute("""
                    DELETE FROM participantes
                    WHERE ci = %s;
                """, (ci,))

                conn.commit()
                flash("Participante eliminado, sanciones desactivadas y asistencia anulada.", "success")

            except Exception as e:
                conn.rollback()
                flash(f"Error al eliminar participante: {e}", "error")

            return redirect(url_for("abm_participantes"))


    # ============================================
    # Mostrar participantes actuales
    # ============================================
    # orden alfabetico, pero el admin primero
    cursor.execute("""
        SELECT p.ci, p.nombre, p.apellido, p.email,
            pa.nombre_programa,
            pa.id_facultad,
            f.nombre AS facultad,
            ppa.rol
        FROM participantes p
        LEFT JOIN participantes_programa_academico ppa ON p.ci = ppa.ci_participante
        LEFT JOIN programas_academicos pa ON pa.nombre_programa = ppa.nombre_programa
        LEFT JOIN facultad f ON pa.id_facultad = f.id_facultad
        ORDER BY
            CASE WHEN p.email = 'administrativo@ucu.edu.uy' THEN 0 ELSE 1 END,
            p.apellido ASC,
            p.nombre ASC;

    """)

    participantes = cursor.fetchall()

    return render_template(
        "admin/abm_participantes.html",
        usuario=current_user,
        participantes=participantes,
        facultades=facultades,
        programas_por_facultad=programas_por_facultad
    )



@app.route("/admin/salas", methods=["GET", "POST"])
@login_required
def abm_salas():
    if current_user.email != "administrativo@ucu.edu.uy":
        return redirect(url_for("home"))

    conn = get_connection("administrativo")
    cursor = conn.cursor(dictionary=True)

    # 🔹 Edificios para el select
    cursor.execute("SELECT nombre_edificio FROM edificio ORDER BY nombre_edificio;")
    edificios = [e["nombre_edificio"] for e in cursor.fetchall()]

    # =========================================
    # ALTA
    # =========================================
    if request.method == "POST" and request.form.get("accion") == "agregar":
        nombre_sala = request.form["nombre_sala"]
        edificio = request.form["edificio"]
        tipo_sala = request.form["tipo_sala"]

        try:
            # Longitud máxima
            if len(nombre_sala) == 0 or len(nombre_sala) > 50:
                raise ValueError("longitud")

            # Solo caracteres permitidos:
            # letras, números, espacios, comillas dobles, apóstrofe
            patron = r"^[A-Za-z0-9\s\"']+$"
            if not re.match(patron, nombre_sala):
                raise ValueError("caracteres")

            # Normalización automática
            nombre_sala = normalizar_sala(nombre_sala)

        except ValueError as e:
            if str(e) == "longitud":
                flash("El nombre de la sala debe tener entre 1 y 50 caracteres.", "error")
            else:
                flash("El nombre de la sala contiene caracteres inválidos.", "error")

            return redirect(url_for("abm_salas"))

        # Validar capacidad (entero positivo y <= 60)
        try:
            capacidad = int(request.form["capacidad"])
            if capacidad <= 0 or capacidad > 60:
                raise ValueError
        except ValueError:
            flash("La capacidad debe ser un número entero entre 1 y 60.", "error")
            return redirect(url_for("abm_salas"))

        # Verificar si ya existe una sala con ese nombre y edificio
        cursor.execute("""
            SELECT COUNT(*) AS existe 
            FROM sala 
            WHERE nombre_sala = %s AND edificio = %s;
        """, (nombre_sala, edificio))
        if cursor.fetchone()["existe"] > 0:
            flash("Ya existe una sala con ese nombre en este edificio.", "warning")
            return redirect(url_for("abm_salas"))

        # Insertar si no existe
        try:
            cursor.execute("""
                INSERT INTO sala (nombre_sala, edificio, capacidad, tipo_sala)
                VALUES (%s, %s, %s, %s);
            """, (nombre_sala, edificio, capacidad, tipo_sala))
            conn.commit()
            flash("Sala agregada correctamente.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Error al agregar sala: {e}", "error")


    # =========================================
    # ELIMINAR
    # =========================================
    elif request.method == "POST" and request.form.get("accion") == "eliminar":
        nombre_sala = request.form["nombre_sala"]
        edificio = request.form["edificio"]

        cursor.execute("""
            DELETE FROM sala
            WHERE nombre_sala = %s AND edificio = %s;
        """, (nombre_sala, edificio))
        conn.commit()
        flash("Sala eliminada correctamente", "success")

    # =========================================
    # EDITAR
    # =========================================
    elif request.method == "POST" and request.form.get("accion") == "editar":
        nombre_sala = request.form["nombre_sala"]
        edificio = request.form["edificio"]
        nuevo_tipo = request.form["tipo_sala"]

        # Validar capacidad (entero positivo y <= 60)
        try:
            capacidad = int(request.form["capacidad"])
            if capacidad <= 0 or capacidad > 60:
                raise ValueError
        except ValueError:
            flash("La capacidad debe ser un número entero entre 1 y 60.", "error")
            return redirect(url_for("abm_salas"))

        try:
            cursor.execute("""
                UPDATE sala
                SET capacidad = %s, tipo_sala = %s
                WHERE nombre_sala = %s AND edificio = %s;
            """, (capacidad, nuevo_tipo, nombre_sala, edificio))
            conn.commit()
            flash("Sala modificada correctamente.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Error al modificar sala: {e}", "error")



    # =========================================
    # CONSULTA
    # =========================================
    cursor.execute("""
        SELECT nombre_sala, edificio, capacidad, tipo_sala
        FROM sala
        ORDER BY edificio, nombre_sala;
    """)
    salas = cursor.fetchall()

    return render_template("admin/abm_salas.html", salas=salas, edificios=edificios)


@app.route("/admin/reservas", methods=["GET", "POST"])
@login_required
def abm_reservas():
    if current_user.email != "administrativo@ucu.edu.uy":
        return redirect(url_for("home"))

    conn = get_connection("administrativo")
    cursor = conn.cursor(dictionary=True)

    # 🔹 Obtener edificios y turnos para los selects
    cursor.execute("SELECT nombre_edificio FROM edificio;")
    edificios = [e["nombre_edificio"] for e in cursor.fetchall()]

    cursor.execute("SELECT id_turno, hora_inicio, hora_fin FROM turno;")
    turnos = cursor.fetchall()

    # =========================================
    # ALTA DE RESERVA
    # =========================================
    if request.method == "POST" and request.form.get("accion") == "agregar":
        edificio = request.form["edificio"]
        nombre_sala = request.form["nombre_sala"]
        fecha = request.form["fecha"]
        id_turno = request.form["id_turno"]
        ci_participante = request.form["ci_participante"].strip()

        try:

            # =======================================
            # Verificar que la fecha no haya pasado
            # =======================================
            hoy = date.today()
            fecha_reserva = datetime.strptime(fecha, "%Y-%m-%d").date()

            if fecha_reserva < hoy:
                flash("No se puede crear una reserva en una fecha pasada", "warning")
                return redirect(url_for("abm_reservas"))

            # =======================================
            # Verificar que el turno no haya pasado (si es hoy)
            # =======================================
            if fecha_reserva == hoy:
                cursor.execute("""
                    SELECT TIME_FORMAT(hora_inicio, '%H:%i') AS inicio
                    FROM turno
                    WHERE id_turno = %s;
                """, (id_turno,))
                
                turno = cursor.fetchone()

                if turno:
                    hora_turno = datetime.strptime(turno["inicio"], "%H:%M").time()
                    hora_actual = datetime.now().time()

                    if hora_turno <= hora_actual:
                        flash("No se puede reservar un turno que ya comenzó o ya pasó", "warning")
                        return redirect(url_for("abm_reservas"))
                    
            # =======================================
            # Validar formato de CI (solo números, 7–8 dígitos)
            # =======================================
            if not ci_participante.isdigit() or len(ci_participante) not in (7, 8):
                flash("La CI debe tener solo números y 7 u 8 dígitos", "warning")
                return redirect(url_for("abm_reservas"))

            # =======================================
            # Verificar existencia del participante
            # =======================================
            cursor.execute("SELECT ci FROM participantes WHERE ci = %s;", (ci_participante,))
            participante = cursor.fetchone()
            if not participante:
                flash("No existe ningún participante con esa CI", "error")
                return redirect(url_for("abm_reservas"))

            # 🔹 Nuevo: verificar que esté en un programa académico
            cursor.execute("""
                SELECT 1
                FROM participantes_programa_academico
                WHERE ci_participante = %s;
            """, (ci_participante,))
            pertenece_programa = cursor.fetchone()

            if not pertenece_programa:
                flash("El participante no pertenece a ningún programa académico.", "warning")
                return redirect(url_for("abm_reservas"))

            # =======================================
            # Verificar tipo del participante (grado, posgrado o docente)
            # =======================================
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN ppa.rol = 'Docente' THEN 'Docente'
                        WHEN ppa.rol = 'Estudiante' AND pa.tipo = 'grado' THEN 'Grado'
                        WHEN ppa.rol = 'Estudiante' AND pa.tipo = 'posgrado' THEN 'Posgrado'
                        ELSE 'Desconocido'
                    END AS tipo_persona
                FROM participantes_programa_academico ppa
                JOIN programas_academicos pa ON pa.nombre_programa = ppa.nombre_programa
                WHERE ppa.ci_participante = %s
                LIMIT 1;
            """, (ci_participante,))
            tipo_persona = cursor.fetchone()

            if not tipo_persona:
                flash("No se pudo determinar el tipo de participante.", "error")
                return redirect(url_for("abm_reservas"))

            tipo_persona = tipo_persona["tipo_persona"]

            # =======================================
            # Verificar tipo de sala
            # =======================================
            cursor.execute("""
                SELECT tipo_sala FROM sala
                WHERE nombre_sala = %s AND edificio = %s;
            """, (nombre_sala, edificio))
            tipo_sala = cursor.fetchone()["tipo_sala"]

            if tipo_sala == "Docente" and tipo_persona != "Docente":
                flash("Solo docentes pueden reservar esta sala.", "error")
                return redirect(url_for("abm_reservas"))

            if tipo_sala == "Posgrado" and tipo_persona != "Posgrado":
                flash("Solo estudiantes de posgrado pueden reservar esta sala.", "error")
                return redirect(url_for("abm_reservas"))

            # =======================================
            # Verificar sanciones activas
            # =======================================
            cursor.execute("""
                SELECT 1
                FROM sancion_participante
                WHERE ci_participante = %s
                AND CURDATE() BETWEEN fecha_inicio AND fecha_fin
                AND activa = 1;
            """, (ci_participante,))
            sancionado = cursor.fetchone()

            if sancionado:
                flash("Este participante tiene una sanción activa y no puede realizar reservas.", "error")
                return redirect(url_for("abm_reservas"))

            # =======================================
            # Verificar límite de horas diarias y reservas semanales (solo grado)
            # =======================================
            if tipo_persona == "Grado":
                # Verificar horas diarias (máx. 2 horas)
                cursor.execute("""
                    SELECT COUNT(*) AS cantidad
                    FROM reserva r
                    JOIN turno t ON r.id_turno = t.id_turno
                    JOIN reserva_participante rp ON rp.id_reserva = r.id_reserva
                    WHERE rp.ci_participante = %s
                    AND r.fecha = %s
                    AND r.estado = 'Activa';
                """, (ci_participante, fecha))
                reservas_hoy = cursor.fetchone()["cantidad"]

                if reservas_hoy >= 2:
                    flash("Límite diario alcanzado (máximo 2 horas por día).", "warning")
                    return redirect(url_for("abm_reservas"))

                # Verificar reservas semanales (máx. 3 activas)
                cursor.execute("""
                    SELECT COUNT(*) AS cantidad
                    FROM reserva r
                    JOIN reserva_participante rp ON rp.id_reserva = r.id_reserva
                    WHERE rp.ci_participante = %s
                    AND r.estado = 'Activa'
                    AND WEEK(r.fecha) = WEEK(%s)
                    AND YEAR(r.fecha) = YEAR(%s);
                """, (ci_participante, fecha, fecha))
                reservas_semana = cursor.fetchone()["cantidad"]

                if reservas_semana >= 3:
                    flash("Límite semanal alcanzado (máximo 3 reservas activas por semana).", "warning")
                    return redirect(url_for("abm_reservas"))

            # =======================================
            # Verificar si ya existe reserva activa igual (sala + fecha + turno)
            # =======================================
            cursor.execute("""
                SELECT 1 FROM reserva
                WHERE nombre_sala = %s AND edificio = %s AND fecha = %s AND id_turno = %s
                AND estado IN ('Activa', 'Pendiente');
            """, (nombre_sala, edificio, fecha, id_turno))
            existe = cursor.fetchone()

            if existe:
                flash("Ya existe una reserva activa para esa sala, fecha y turno.", "warning")
                return redirect(url_for("abm_reservas"))

            # =======================================
            # Insertar reserva y asociar participante
            # =======================================
            cursor.execute("""
                INSERT INTO reserva (nombre_sala, edificio, fecha, id_turno, estado)
                VALUES (%s, %s, %s, %s, 'Activa');
            """, (nombre_sala, edificio, fecha, id_turno))
            conn.commit()

            cursor.execute("SELECT LAST_INSERT_ID() AS id_reserva;")
            nueva_reserva = cursor.fetchone()["id_reserva"]

            cursor.execute("""
                INSERT INTO reserva_participante (ci_participante, id_reserva, fecha_solicitud_reserva, asistencia)
                VALUES (%s, %s, NOW(), FALSE);
            """, (ci_participante, nueva_reserva))
            conn.commit()

            flash("Reserva creada correctamente y participante asociado.", "success")

        except Exception as e:
            conn.rollback()
            flash(f"Error al crear la reserva: {e}", "error")

    # =========================================
    # MODIFICAR RESERVA
    # =========================================
    if request.method == "POST" and request.form.get("accion") == "modificar":
        id_reserva = request.form.get("id_reserva")
        nuevo_estado = request.form.get("estado_nuevo")
        id_turno_nuevo = request.form.get("id_turno_nuevo")
        fecha_nueva = request.form.get("fecha_nueva")

        try:
            # Obtener datos actuales
            cursor.execute("""
                SELECT nombre_sala, edificio
                FROM reserva
                WHERE id_reserva = %s;
            """, (id_reserva,))
            datos = cursor.fetchone()

            if not datos:
                flash("No se encontró la reserva seleccionada.", "error")
            else:
                nombre_sala = datos["nombre_sala"]
                edificio = datos["edificio"]

                # =======================================
                # Validar fecha nueva (no pasada)
                # =======================================
                hoy = date.today()
                fecha_modificada = datetime.strptime(fecha_nueva, "%Y-%m-%d").date()

                if fecha_modificada < hoy:
                    flash("No se puede mover la reserva a una fecha pasada.", "warning")
                    return redirect(url_for("abm_reservas"))


                # =======================================
                # Validar turno si la fecha nueva es hoy
                # =======================================
                if fecha_modificada == hoy:
                    cursor.execute("""
                        SELECT TIME_FORMAT(hora_inicio, '%H:%i') AS inicio
                        FROM turno
                        WHERE id_turno = %s;
                    """, (id_turno_nuevo,))

                    turno = cursor.fetchone()

                    if turno:
                        hora_turno = datetime.strptime(turno["inicio"], "%H:%M").time()
                        hora_actual = datetime.now().time()

                        if hora_turno <= hora_actual:
                            flash("No se puede mover la reserva a un turno que ya pasó.", "warning")
                            return redirect(url_for("abm_reservas"))

                # Verificar si ya hay reserva activa con esa misma sala, edificio, fecha y turno
                cursor.execute("""
                    SELECT 1 FROM reserva
                    WHERE nombre_sala = %s
                    AND edificio = %s
                    AND fecha = %s
                    AND id_turno = %s
                    AND estado = 'Activa'
                    AND id_reserva <> %s;
                """, (nombre_sala, edificio, fecha_nueva, id_turno_nuevo, id_reserva))
                ocupada = cursor.fetchone()

                if ocupada:
                    flash("Ya existe una reserva activa en esa sala, fecha y turno.", "warning")
                else:
                    # Actualizar la reserva (fecha, turno y estado)
                    cursor.execute("""
                        UPDATE reserva
                        SET fecha = %s, id_turno = %s, estado = %s
                        WHERE id_reserva = %s;
                    """, (fecha_nueva, id_turno_nuevo, nuevo_estado, id_reserva))
                    conn.commit()

                    flash("Reserva actualizada correctamente.", "success")
                    # Notificar a todos los participantes
                    cursor.execute("SELECT ci_participante FROM reserva_participante WHERE id_reserva = %s", (id_reserva,))
                    for p in cursor.fetchall():
                        crear_notificacion(cursor, p["ci_participante"], f"La reserva #{id_reserva} fue modificada por un administrador.")
                    conn.commit()


                    # 🔹 Si se canceló, borrar los participantes asociados
                    if nuevo_estado.lower() == "cancelada":
                        cursor.execute("""
                            DELETE FROM reserva_participante WHERE id_reserva = %s;
                        """, (id_reserva,))
                        conn.commit()
                        flash("Reserva cancelada y participantes eliminados.", "success")

        except Exception as e:
            conn.rollback()
            flash(f"Error al modificar la reserva: {e}", "error")

    # =========================================
    # LISTADO DE RESERVAS
    # =========================================
    cursor.execute("""
        SELECT r.id_reserva, r.id_turno, r.fecha, 
            t.hora_inicio, t.hora_fin,
            r.estado, r.nombre_sala, r.edificio,
            s.capacidad,
            COUNT(rp.ci_participante) AS ocupacion
        FROM reserva r
        JOIN turno t ON r.id_turno = t.id_turno
        JOIN sala s ON r.nombre_sala = s.nombre_sala AND r.edificio = s.edificio
        LEFT JOIN reserva_participante rp ON r.id_reserva = rp.id_reserva
        WHERE r.estado = 'Activa'
        GROUP BY r.id_reserva
        ORDER BY r.id_reserva ASC;
    """)
    reservas = cursor.fetchall()

    # 🔹 Obtener salas filtradas por edificio (para JS dinámico)
    cursor.execute("""
        SELECT nombre_sala, edificio
        FROM sala;
    """)
    salas_por_edificio = {}
    for row in cursor.fetchall():
        salas_por_edificio.setdefault(row["edificio"], []).append(row["nombre_sala"])

    conn.close()
    return render_template("admin/abm_reservas.html",
                           reservas=reservas,
                           edificios=edificios,
                           turnos=turnos,
                           salas_por_edificio=salas_por_edificio)

@app.route("/admin/reservas/participantes", methods=["GET", "POST"])
@login_required
def abm_reservas_participantes():
    if current_user.email != "administrativo@ucu.edu.uy":
        return redirect(url_for("home"))

    conn = get_connection("administrativo")
    cursor = conn.cursor(dictionary=True)

    participantes = []
    reserva_info = None

    if request.method == "POST":
        accion = request.form.get("accion")
        id_reserva = request.form.get("id_reserva")

        # ===============================
        #  VERIFICAR QUE LA RESERVA EXISTA
        # ===============================
        cursor.execute("""
            SELECT r.id_reserva, r.nombre_sala, r.edificio, r.fecha,
                   t.hora_inicio, t.hora_fin,
                   s.capacidad, s.tipo_sala,
                   r.estado
            FROM reserva r
            JOIN turno t ON r.id_turno = t.id_turno
            JOIN sala s ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
            WHERE r.id_reserva = %s;
        """, (id_reserva,))
        reserva_info = cursor.fetchone()

        if not reserva_info:
            flash("No existe una reserva con ese ID.", "error")
            return render_template("admin/abm_reservas-participantes.html")

        estado = reserva_info["estado"].lower()

        # =========================================
        # BLOQUEAR TODA MODIFICACIÓN SI NO ESTÁ ACTIVA
        # =========================================
        if estado != "activa":
            flash(f"No se pueden modificar los participantes porque la reserva está '{reserva_info['estado']}'.", "warning")

            cursor.execute("""
                SELECT rp.ci_participante, p.nombre, p.apellido
                FROM reserva_participante rp
                JOIN participantes p ON p.ci = rp.ci_participante
                WHERE rp.id_reserva = %s;
            """, (id_reserva,))
            participantes = cursor.fetchall()

            conn.close()
            return render_template(
                "admin/abm_reservas-participantes.html",
                reserva=reserva_info,
                participantes=participantes
            )

        # =========================================
        #  A PARTIR DE ACÁ SOLO SI ESTÁ ACTIVA
        # =========================================

        # -------------------------
        # ELIMINAR PARTICIPANTE
        # -------------------------
        if accion == "eliminar":
            ci = request.form.get("ci_participante")

            cursor.execute("""
                DELETE FROM reserva_participante
                WHERE id_reserva = %s AND ci_participante = %s;
            """, (id_reserva, ci))
            conn.commit()

            # Verificar si quedó vacía
            cursor.execute("""
                SELECT COUNT(*) AS cant
                FROM reserva_participante
                WHERE id_reserva = %s;
            """, (id_reserva,))
            cant = cursor.fetchone()["cant"]

            if cant == 0:
                cursor.execute("""
                    UPDATE reserva
                    SET estado = 'Cancelada'
                    WHERE id_reserva = %s;
                """, (id_reserva,))
                conn.commit()

                flash("Participante eliminado. La reserva quedó vacía y fue cancelada.", "success")
            else:
                flash("Participante eliminado correctamente.", "success")

        # -------------------------
        # AGREGAR PARTICIPANTE
        # -------------------------
        elif accion == "agregar":
            ci_nuevo = request.form.get("ci_nuevo").strip()

            # Validar CI
            if not ci_nuevo.isdigit() or len(ci_nuevo) not in (7, 8):
                flash("La cédula ingresada debe tener 7 u 8 dígitos", "warning")

            else:
                # Verificar existencia
                cursor.execute("SELECT ci FROM participantes WHERE ci = %s;", (ci_nuevo,))
                existe = cursor.fetchone()

                if not existe:
                    flash("No existe un participante con esa CI", "error")

                else:
                    # Verificar que esté en programa académico
                    cursor.execute("""
                        SELECT 1
                        FROM participantes_programa_academico
                        WHERE ci_participante = %s;
                    """, (ci_nuevo,))
                    pertenece = cursor.fetchone()

                    if not pertenece:
                        flash("El participante no pertenece a ningún programa académico", "warning")

                    else:
                        # Tipo de persona
                        cursor.execute("""
                            SELECT 
                                CASE 
                                    WHEN ppa.rol = 'Docente' THEN 'Docente'
                                    WHEN ppa.rol = 'Estudiante' AND pa.tipo = 'grado' THEN 'Grado'
                                    WHEN ppa.rol = 'Estudiante' AND pa.tipo = 'posgrado' THEN 'Posgrado'
                                END AS tipo_persona
                            FROM participantes_programa_academico ppa
                            JOIN programas_academicos pa ON pa.nombre_programa = ppa.nombre_programa
                            WHERE ppa.ci_participante = %s
                            LIMIT 1;
                        """, (ci_nuevo,))
                        tipo_persona = cursor.fetchone()["tipo_persona"]

                        tipo_sala = reserva_info["tipo_sala"]

                        # Restricciones por tipo de sala
                        if tipo_sala == "Docente" and tipo_persona != "Docente":
                            flash("Solo docentes pueden usar esta sala", "error")

                        elif tipo_sala == "Posgrado" and tipo_persona != "Posgrado":
                            flash("Solo estudiantes de posgrado pueden estar en esta sala", "error")

                        else:
                            # Sanción activa
                            cursor.execute("""
                                SELECT 1 FROM sancion_participante
                                WHERE ci_participante = %s
                                AND CURDATE() BETWEEN fecha_inicio AND fecha_fin
                                AND activa = 1;
                            """, (ci_nuevo,))
                            sancionado = cursor.fetchone()

                            if sancionado:
                                flash("El participante tiene una sanción activa", "error")

                            else:
                                # Capacidad
                                cursor.execute("""
                                    SELECT COUNT(*) AS ocupados
                                    FROM reserva_participante
                                    WHERE id_reserva = %s;
                                """, (id_reserva,))
                                ocupados = cursor.fetchone()["ocupados"]

                                if ocupados >= reserva_info["capacidad"]:
                                    flash("La sala está llena.", "warning")
                                else:
                                    # Verificar si ya está
                                    cursor.execute("""
                                        SELECT 1 FROM reserva_participante
                                        WHERE ci_participante = %s AND id_reserva = %s;
                                    """, (ci_nuevo, id_reserva))
                                    ya_esta = cursor.fetchone()

                                    if ya_esta:
                                        flash("Este participante ya está en la reserva", "warning")
                                    else:
                                        # Insertar
                                        cursor.execute("""
                                            INSERT INTO reserva_participante 
                                            (ci_participante, id_reserva, fecha_solicitud_reserva, asistencia)
                                            VALUES (%s, %s, NOW(), FALSE);
                                        """, (ci_nuevo, id_reserva))
                                        conn.commit()
                                        flash("Participante agregado correctamente", "success")

        # -------------------------
        # OBTENER PARTICIPANTES
        # -------------------------
        cursor.execute("""
            SELECT rp.ci_participante, p.nombre, p.apellido
            FROM reserva_participante rp
            JOIN participantes p ON p.ci = rp.ci_participante
            WHERE rp.id_reserva = %s AND confirmado=1;
        """, (id_reserva,))
        participantes = cursor.fetchall()

    conn.close()
    return render_template(
        "admin/abm_reservas-participantes.html",
        reserva=reserva_info,
        participantes=participantes
    )



from datetime import datetime, timedelta

@app.route("/admin/asistencias", methods=["GET", "POST"])
@login_required
def asistencias():
    if current_user.email != "administrativo@ucu.edu.uy":
        return redirect(url_for("home"))

    conn = get_connection("administrativo")
    cursor = conn.cursor(dictionary=True)

    participantes = []
    reserva_info = None
    editable = False  # <-- NUEVO

    if request.method == "POST":
        accion = request.form.get("accion")
        id_reserva = request.form.get("id_reserva")

        # Obtener reserva
        cursor.execute("""
            SELECT r.id_reserva, r.nombre_sala, r.edificio, r.fecha,
                   t.hora_inicio, t.hora_fin, s.capacidad, s.tipo_sala, r.estado
            FROM reserva r
            JOIN turno t ON r.id_turno = t.id_turno
            JOIN sala s ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
            WHERE r.id_reserva = %s;
        """, (id_reserva,))
        reserva_info = cursor.fetchone()

        if not reserva_info:
            flash("No existe una reserva con ese ID.", "error")
            return render_template("admin/asistencias.html")

        estado = reserva_info["estado"].lower()

        # =============================
        # BLOQUEAR POR ESTADO
        # =============================
        if estado != "activa":
            editable = False
        else:
            # =============================
            # BLOQUEAR POR TIEMPO (10 MIN)
            # =============================
            fecha = reserva_info["fecha"]
            hora_fin_raw = reserva_info["hora_fin"]

            if isinstance(hora_fin_raw, timedelta):
                total_seconds = int(hora_fin_raw.total_seconds())
                horas = total_seconds // 3600
                minutos = (total_seconds % 3600) // 60
                segundos = total_seconds % 60
                hora_fin = time(horas, minutos, segundos)
            else:
                hora_fin = hora_fin_raw

            dt_fin = datetime.combine(fecha, hora_fin)
            limite = dt_fin + timedelta(minutes=10)
            ahora = datetime.now()

            editable = ahora <= limite


        # ============================================
        # GUARDAR ASISTENCIAS SI ES EDITABLE
        # ============================================
        if accion == "guardar":
            if not editable:
                flash("La reserva ya no puede editarse (pasaron más de 10 minutos).", "warning")
            else:
                cursor.execute("""
                    SELECT ci_participante
                    FROM reserva_participante
                    WHERE id_reserva = %s;
                """, (id_reserva,))
                todos = cursor.fetchall()

                for p in todos:
                    ci = p["ci_participante"]
                    asistencia = request.form.get(f"asistencia_{ci}", "0")

                    cursor.execute("""
                        UPDATE reserva_participante
                        SET asistencia = %s
                        WHERE id_reserva = %s AND ci_participante = %s;
                    """, (asistencia, id_reserva, ci))

                conn.commit()
                flash("Asistencias actualizadas correctamente.", "success")

        # Obtener lista actualizada
        cursor.execute("""
            SELECT rp.ci_participante, p.nombre, p.apellido, rp.asistencia
            FROM reserva_participante rp
            JOIN participantes p ON p.ci = rp.ci_participante
            WHERE rp.id_reserva = %s;
        """, (id_reserva,))
        participantes = cursor.fetchall()

    conn.close()
    return render_template(
        "admin/asistencias.html",
        reserva=reserva_info,
        participantes=participantes,
        editable=editable  # <-- ENVIAMOS ESTADO A HTML
    )






@app.route("/admin/sanciones", methods=["GET", "POST"])
@login_required
def abm_sanciones():
    if current_user.email != "administrativo@ucu.edu.uy":
        return redirect(url_for("home"))

    conn = get_connection("administrativo")
    cursor = conn.cursor(dictionary=True)

    # ===============================
    # ALTA
    # ===============================
    if request.method == "POST" and request.form.get("accion") == "agregar":
        ci_participante = request.form["ci_participante"].strip()

        # El inicio SIEMPRE es hoy
        fecha_inicio_dt = date.today()

        fecha_fin = request.form["fecha_fin"]

        try:
            fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
        except ValueError:
            flash("Formato de fecha inválido.", "error")
            return redirect(url_for("abm_sanciones"))

        # NO permitir fecha fin menor que hoy
        if fecha_fin_dt < fecha_inicio_dt:
            flash("La fecha de fin no puede ser menor que la fecha de inicio (hoy).", "error")
            return redirect(url_for("abm_sanciones"))

        # Validar CI
        if not ci_participante.isdigit() or len(ci_participante) not in (7, 8):
            flash("La cédula ingresada debe tener 7 u 8 dígitos", "warning")
            return redirect(url_for("abm_sanciones"))

        # Validar existencia del participante
        cursor.execute("SELECT 1 FROM participantes WHERE ci = %s;", (ci_participante,))
        participante = cursor.fetchone()

        if not participante:
            flash("No existe un participante con esa cédula", "error")
            return redirect(url_for("abm_sanciones"))

        # Validar vínculo académico
        cursor.execute("""
            SELECT 1 
            FROM participantes_programa_academico
            WHERE ci_participante = %s LIMIT 1;
        """, (ci_participante,))
        vinculado = cursor.fetchone()

        if not vinculado:
            flash("El participante no está vinculado a ningún programa académico", "error")
            return redirect(url_for("abm_sanciones"))

        # ==========================================================
        # 1) BUSCAR TODAS LAS SANCIONES QUE SE SUPERPONGAN O TOQUEN
        # ==========================================================
        cursor.execute("""
            SELECT fecha_inicio, fecha_fin
            FROM sancion_participante
            WHERE ci_participante = %s
            AND activa = TRUE
            AND (
                (fecha_inicio <= %s AND fecha_fin >= %s)         -- superposición
                OR fecha_fin = DATE_SUB(%s, INTERVAL 1 DAY)      -- contigua atrás
                OR fecha_inicio = DATE_ADD(%s, INTERVAL 1 DAY)   -- contigua adelante
            );
        """, (
            ci_participante,
            fecha_fin_dt,
            fecha_inicio_dt,
            fecha_inicio_dt,
            fecha_fin_dt
        ))

        sanciones_relacionadas = cursor.fetchall()

        # ==========================================================
        # 2) SI HAY SANCIONES PARA MERGEAR → FUSIONAR
        # ==========================================================
        if sanciones_relacionadas:
            nuevo_inicio = min([s["fecha_inicio"] for s in sanciones_relacionadas] + [fecha_inicio_dt])
            nuevo_fin = max([s["fecha_fin"] for s in sanciones_relacionadas] + [fecha_fin_dt])

            try:
                cursor.execute("""
                    DELETE FROM sancion_participante
                    WHERE ci_participante = %s
                    AND activa = TRUE
                    AND (
                        (fecha_inicio <= %s AND fecha_fin >= %s)
                        OR fecha_fin = DATE_SUB(%s, INTERVAL 1 DAY)
                        OR fecha_inicio = DATE_ADD(%s, INTERVAL 1 DAY)
                    );
                """, (
                    ci_participante,
                    fecha_fin_dt,
                    fecha_inicio_dt,
                    fecha_inicio_dt,
                    fecha_fin_dt
                ))

                cursor.execute("""
                    INSERT INTO sancion_participante (ci_participante, fecha_inicio, fecha_fin)
                    VALUES (%s, %s, %s);
                """, (ci_participante, nuevo_inicio, nuevo_fin))

                conn.commit()
                flash("Sanciones fusionadas correctamente.", "success")
                return redirect(url_for("abm_sanciones"))

            except Exception as e:
                conn.rollback()
                flash(f"Error al mergear sanciones: {e}", "error")
                return redirect(url_for("abm_sanciones"))

        # ==========================================================
        # 3) SI NO HUBO MERGE → INSERTAR SANCIÓN NORMAL
        # ==========================================================
        try:
            cursor.execute("""
                INSERT INTO sancion_participante (ci_participante, fecha_inicio, fecha_fin)
                VALUES (%s, %s, %s);
            """, (ci_participante, fecha_inicio_dt, fecha_fin_dt))

            conn.commit()
            flash("Sanción agregada correctamente.", "success")

            crear_notificacion(cursor, ci_participante, "Recibiste una sanción por inasistencia.")
            conn.commit()


        except Exception as e:
            conn.rollback()
            flash(f"Error al agregar sanción: {e}", "error")




    # ===============================
    # EDITAR SANCIÓN
    # ===============================

    if request.method == "POST" and request.form.get("accion") == "editar":
        ci_participante = request.form["ci_participante"]
        fecha_inicio_str = request.form["fecha_inicio"]  # viene como string
        nueva_fecha_fin_str = request.form["fecha_fin"]
        nueva_activa = request.form["activa"]

        # Convertir a date
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            nueva_fecha_fin_dt = datetime.strptime(nueva_fecha_fin_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Formato de fecha inválido.", "error")
            return redirect(url_for("abm_sanciones"))

        # Validar que la nueva fecha fin NO sea menor que la fecha inicio
        if nueva_fecha_fin_dt < fecha_inicio_dt:
            flash("La nueva fecha de fin no puede ser menor que la fecha de inicio.", "error")
            return redirect(url_for("abm_sanciones"))

        try:
            cursor.execute("""
                UPDATE sancion_participante
                SET fecha_fin = %s,
                    activa = %s
                WHERE ci_participante = %s AND fecha_inicio = %s;
            """, (nueva_fecha_fin_dt, nueva_activa, ci_participante, fecha_inicio_dt))
            
            conn.commit()
            flash("Sanción actualizada correctamente", "success")

        except Exception as e:
            conn.rollback()
            flash(f"Error al modificar sanción: {e}", "error")


    # ===============================
    # MOSTRAR SOLO ACTIVAS
    # ===============================
    cursor.execute("""
        SELECT 
            sp.ci_participante,
            p.nombre,
            p.apellido,
            sp.fecha_inicio,
            sp.fecha_fin,
            sp.activa,
            CASE
                WHEN CURDATE() < sp.fecha_inicio THEN 'Pendiente'
                WHEN CURDATE() BETWEEN sp.fecha_inicio AND sp.fecha_fin THEN 'Activa'
            END AS estado
        FROM sancion_participante sp
        JOIN participantes p ON p.ci = sp.ci_participante
        WHERE sp.activa = TRUE
        AND sp.fecha_fin >= CURDATE()
        ORDER BY sp.fecha_inicio DESC;

    """)

    sanciones = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin/abm_sanciones.html", usuario=current_user, sanciones=sanciones, hoy=date.today())








@app.route("/admin/reportes")
@login_required
def reportes():
    if current_user.email != "administrativo@ucu.edu.uy":
        return redirect(url_for("home"))

    return render_template("admin/reportes.html", usuario=current_user)




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
    hash_existing_passwords()
    app.run(host="0.0.0.0", port=5000, debug=True)


