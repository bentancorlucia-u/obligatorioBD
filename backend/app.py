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
from werkzeug.security import generate_password_hash
from utilidades import (
    generar_contrasena,
    validar_cedula_uruguaya,
    validar_email_institucional
)
from reportes import reportes_bp

from hash_existing_passwords import hash_existing_passwords

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
    # 🔒 Solo el admin puede acceder
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

            # Validaciones
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

            # Evitar modificar al admin
            if email == "administrativo@ucu.edu.uy":
                flash("No se puede modificar al usuario administrativo.", "warning")
                return redirect(url_for("abm_participantes"))

            try:
                cursor.execute("""
                    UPDATE participantes
                    SET nombre = %s, apellido = %s, email = %s
                    WHERE ci = %s
                """, (nombre, apellido, email, ci))
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

            email = participante["email"]

            # Evitar eliminar al admin
            if email == "administrativo@ucu.edu.uy":
                flash("No se puede eliminar al usuario administrativo.", "warning")
                return redirect(url_for("abm_participantes"))

            try:
                cursor.execute("DELETE FROM participantes WHERE ci = %s", (ci,))
                conn.commit()
                flash("Participante eliminado correctamente.", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Error al eliminar participante: {e}", "error")

            return redirect(url_for("abm_participantes"))

    # ============================================
    # Mostrar participantes actuales
    # ============================================
    cursor.execute("""
        SELECT ci, nombre, apellido, email
        FROM participantes
        ORDER BY 
            CASE WHEN email = 'administrativo@ucu.edu.uy' THEN 0 ELSE 1 END,
            apellido, nombre;
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

        # Validar capacidad (entero positivo)
        try:
            capacidad = int(request.form["capacidad"])
            if capacidad <= 0:
                raise ValueError
        except ValueError:
            flash("La capacidad debe ser un número entero positivo.", "error")
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
        flash("Sala eliminada correctamente.", "info")

    # =========================================
    # EDITAR
    # =========================================
    elif request.method == "POST" and request.form.get("accion") == "editar":
        nombre_sala = request.form["nombre_sala"]
        edificio = request.form["edificio"]
        nuevo_tipo = request.form["tipo_sala"]

        # Validar capacidad
        try:
            nueva_capacidad = int(request.form["capacidad"])
            if nueva_capacidad <= 0:
                raise ValueError("Capacidad debe ser un número entero positivo.")
        except ValueError:
            flash("La capacidad debe ser un número entero positivo.", "error")
            return redirect(url_for("abm_salas"))

        try:
            cursor.execute("""
                UPDATE sala
                SET capacidad = %s, tipo_sala = %s
                WHERE nombre_sala = %s AND edificio = %s;
            """, (nueva_capacidad, nuevo_tipo, nombre_sala, edificio))
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
            # Validar formato de CI (solo números, 7–8 dígitos)
            # =======================================
            if not ci_participante.isdigit() or len(ci_participante) not in (7, 8):
                flash("La CI debe tener solo números y 7 u 8 dígitos.", "warning")
                return redirect(url_for("abm_reservas"))

            # =======================================
            # Verificar existencia del participante
            # =======================================
            cursor.execute("SELECT ci FROM participantes WHERE ci = %s;", (ci_participante,))
            participante = cursor.fetchone()
            if not participante:
                flash("No existe ningún participante con esa CI.", "error")
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
                AND CURDATE() BETWEEN fecha_inicio AND fecha_fin;
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
                VALUES (%s, %s, NOW(), TRUE);
            """, (ci_participante, nueva_reserva))
            conn.commit()

            flash("Reserva creada correctamente y participante asociado.", "success")

        except Exception as e:
            conn.rollback()
            flash(f"Error al crear la reserva: {e}", "error")


    # =========================================
    # BAJA DE RESERVA
    # =========================================
    if request.method == "POST" and request.form.get("accion") == "eliminar":
        id_reserva = request.form["id_reserva"]
        try:
            # Cambiar estado a Cancelada
            cursor.execute("""
                UPDATE reserva
                SET estado = 'Cancelada'
                WHERE id_reserva = %s;
            """, (id_reserva,))

            # Eliminar los participantes asociados
            cursor.execute("""
                DELETE FROM reserva_participante
                WHERE id_reserva = %s;
            """, (id_reserva,))

            conn.commit()
            flash("Reserva cancelada y participantes eliminados correctamente.", "success")

        except Exception as e:
            conn.rollback()
            flash(f"Error al cancelar la reserva: {e}", "error")

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
                    flash("⚠️ Ya existe una reserva activa en esa sala, fecha y turno.", "warning")
                else:
                    # Actualizar la reserva (fecha, turno y estado)
                    cursor.execute("""
                        UPDATE reserva
                        SET fecha = %s, id_turno = %s, estado = %s
                        WHERE id_reserva = %s;
                    """, (fecha_nueva, id_turno_nuevo, nuevo_estado, id_reserva))
                    conn.commit()

                    flash("Reserva actualizada correctamente.", "success")

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
        ORDER BY r.fecha DESC;
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

        # 🔹 Verificar que la reserva exista
        cursor.execute("""
            SELECT r.id_reserva, r.nombre_sala, r.edificio, r.fecha, t.hora_inicio, t.hora_fin, s.capacidad, s.tipo_sala
            FROM reserva r
            JOIN turno t ON r.id_turno = t.id_turno
            JOIN sala s ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
            WHERE r.id_reserva = %s;
        """, (id_reserva,))
        reserva_info = cursor.fetchone()

        if not reserva_info:
            flash("No existe una reserva con ese ID.", "error")
            return render_template("admin/abm_reservas-participantes.html")

        # 🔹 Eliminar participante
        if accion == "eliminar":
            ci = request.form.get("ci_participante")
            cursor.execute("""
                DELETE FROM reserva_participante
                WHERE id_reserva = %s AND ci_participante = %s;
            """, (id_reserva, ci))
            conn.commit()
            flash("Participante eliminado correctamente.", "success")

        # 🔹 Agregar participante (con validaciones)
        elif accion == "agregar":
            ci_nuevo = request.form.get("ci_nuevo").strip()

            # Validar formato CI
            if not ci_nuevo.isdigit() or len(ci_nuevo) not in (7, 8):
                flash("La CI debe tener solo números (7 u 8 dígitos).", "warning")
            else:
                # Verificar existencia
                cursor.execute("SELECT ci FROM participantes WHERE ci = %s;", (ci_nuevo,))
                participante = cursor.fetchone()

                if not participante:
                    flash("No existe ningún participante con esa CI.", "error")
                else:
                    # 🔹 Verificar que esté inscripto en un programa académico
                    cursor.execute("""
                        SELECT 1
                        FROM participantes_programa_academico
                        WHERE ci_participante = %s;
                    """, (ci_nuevo,))
                    pertenece_programa = cursor.fetchone()

                    if not pertenece_programa:
                        flash("El participante no pertenece a ningún programa académico.", "warning")
                    else:
                    
                        try:
                            # Tipo de persona
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
                            """, (ci_nuevo,))
                            tipo_persona = cursor.fetchone()["tipo_persona"]

                            tipo_sala = reserva_info["tipo_sala"]

                            # Restricciones por tipo de sala
                            if tipo_sala == "Docente" and tipo_persona != "Docente":
                                flash("Solo docentes pueden estar en esta sala.", "error")
                            elif tipo_sala == "Posgrado" and tipo_persona != "Posgrado":
                                flash("Solo estudiantes de posgrado pueden estar en esta sala", "error")
                            else:
                                # Sanción activa
                                cursor.execute("""
                                    SELECT 1 FROM sancion_participante
                                    WHERE ci_participante = %s
                                    AND CURDATE() BETWEEN fecha_inicio AND fecha_fin;
                                """, (ci_nuevo,))
                                sancionado = cursor.fetchone()

                                if sancionado:
                                    flash("Este participante tiene una sanción activa.", "error")
                                else:
                                    # Capacidad de la sala
                                    cursor.execute("""
                                        SELECT COUNT(*) AS ocupados
                                        FROM reserva_participante
                                        WHERE id_reserva = %s;
                                    """, (id_reserva,))
                                    ocupados = cursor.fetchone()["ocupados"]

                                    if ocupados >= reserva_info["capacidad"]:
                                        flash("No se puede agregar: sala al límite de capacidad.", "warning")
                                    else:
                                        # Verificar si ya está en la reserva
                                        cursor.execute("""
                                            SELECT 1 FROM reserva_participante
                                            WHERE ci_participante = %s AND id_reserva = %s;
                                        """, (ci_nuevo, id_reserva))
                                        ya_esta = cursor.fetchone()

                                        if ya_esta:
                                            flash("Ese participante ya está asociado a esta reserva.", "warning")
                                        else:
                                            cursor.execute("""
                                                INSERT INTO reserva_participante (ci_participante, id_reserva, fecha_solicitud_reserva, asistencia)
                                                VALUES (%s, %s, NOW(), TRUE);
                                            """, (ci_nuevo, id_reserva))
                                            conn.commit()
                                            flash("Participante agregado correctamente.", "success")

                        except Exception as e:
                            flash(f"Error al agregar participante: {e}", "error")

        # 🔹 Obtener lista actualizada de participantes
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


@app.route("/admin/asistencias", methods=["GET", "POST"])
@login_required
def asistencias():
    if current_user.email != "administrativo@ucu.edu.uy":
        return redirect(url_for("home"))

    conn = get_connection("administrativo")
    cursor = conn.cursor(dictionary=True)

    participantes = []
    reserva_info = None

    if request.method == "POST":
        accion = request.form.get("accion")
        id_reserva = request.form.get("id_reserva")

        # 🔹 Verificar que la reserva exista
        cursor.execute("""
            SELECT r.id_reserva, r.nombre_sala, r.edificio, r.fecha, 
                   t.hora_inicio, t.hora_fin, s.capacidad, s.tipo_sala
            FROM reserva r
            JOIN turno t ON r.id_turno = t.id_turno
            JOIN sala s ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
            WHERE r.id_reserva = %s;
        """, (id_reserva,))
        reserva_info = cursor.fetchone()

        if not reserva_info:
            flash("No existe una reserva con ese ID.", "error")
            return render_template("admin/asistencias.html")

        # 🔹 Guardar asistencias
        if accion == "guardar":
            for key, value in request.form.items():
                if key.startswith("asistencia_"):
                    ci = key.split("_")[1]
                    asistencia = 1 if value == "on" else 0
                    cursor.execute("""
                        UPDATE reserva_participante
                        SET asistencia = %s
                        WHERE id_reserva = %s AND ci_participante = %s;
                    """, (asistencia, id_reserva, ci))
            conn.commit()
            flash("Asistencias actualizadas correctamente.", "success")

        # 🔹 Obtener lista actualizada de participantes con asistencia
        cursor.execute("""
            SELECT rp.ci_participante, p.nombre, p.apellido, rp.asistencia
            FROM reserva_participante rp
            JOIN participantes p ON p.ci = rp.ci_participante
            WHERE rp.id_reserva = %s;
        """, (id_reserva,))
        participantes = cursor.fetchall()

        if not participantes:
            flash("No se encontraron participantes para el ID ingresado.", "warning")

    conn.close()
    return render_template(
        "admin/asistencias.html",
        reserva=reserva_info,
        participantes=participantes
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
        fecha_inicio = request.form["fecha_inicio"]
        fecha_fin = request.form["fecha_fin"]

        # 1️⃣ Validar formato uruguayo
        if not validar_cedula_uruguaya(ci_participante):
            flash("La cédula ingresada no es válida según el formato uruguayo.", "error")

        else:
            # 2️⃣ Validar existencia en participantes
            cursor.execute("SELECT * FROM participantes WHERE ci = %s;", (ci_participante,))
            participante = cursor.fetchone()

            if not participante:
                flash("No existe un participante con esa cédula.", "error")
            else:
                # 3️⃣ Validar vínculo académico
                cursor.execute("""
                    SELECT 1 FROM participantes_programa_academico
                    WHERE ci_participante = %s LIMIT 1;
                """, (ci_participante,))
                vinculado = cursor.fetchone()

                if not vinculado:
                    flash("El participante no está vinculado a ningún programa académico.", "error")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO sancion_participante (ci_participante, fecha_inicio, fecha_fin)
                            VALUES (%s, %s, %s);
                        """, (ci_participante, fecha_inicio, fecha_fin))
                        conn.commit()
                        flash("Sanción agregada correctamente.", "success")
                    except Exception as e:
                        conn.rollback()
                        flash(f"Error al agregar sanción: {e}", "error")

    # ===============================
    # EDITAR Y ELIMINAR IGUAL QUE ANTES
    # ===============================

    if request.method == "POST" and request.form.get("accion") == "editar":
        ci_participante = request.form["ci_participante"]
        fecha_inicio = request.form["fecha_inicio"]
        nueva_fecha_fin = request.form["fecha_fin"]

        try:
            cursor.execute("""
                UPDATE sancion_participante
                SET fecha_fin = %s
                WHERE ci_participante = %s AND fecha_inicio = %s;
            """, (nueva_fecha_fin, ci_participante, fecha_inicio))
            conn.commit()
            flash("Fecha de fin actualizada correctamente.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Error al modificar sanción: {e}", "error")

    if request.method == "POST" and request.form.get("accion") == "eliminar":
        ci_participante = request.form["ci_participante"]
        fecha_inicio = request.form["fecha_inicio"]

        try:
            cursor.execute("""
                DELETE FROM sancion_participante
                WHERE ci_participante = %s AND fecha_inicio = %s;
            """, (ci_participante, fecha_inicio))
            conn.commit()
            flash("Sanción eliminada correctamente.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Error al eliminar sanción: {e}", "error")

    # ===============================
    # MOSTRAR SOLO ACTIVAS
    # ===============================
    cursor.execute("""
        SELECT 
            sp.ci_participante,
            p.nombre,
            p.apellido,
            sp.fecha_inicio,
            sp.fecha_fin
        FROM sancion_participante sp
        JOIN participantes p ON p.ci = sp.ci_participante
        WHERE CURDATE() BETWEEN sp.fecha_inicio AND sp.fecha_fin
        ORDER BY sp.fecha_inicio DESC;
    """)
    sanciones = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin/abm_sanciones.html", usuario=current_user, sanciones=sanciones)








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
    csrf.init_app(app)
    app.run(debug=True)

