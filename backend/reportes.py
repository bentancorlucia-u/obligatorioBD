# ===========================
# Reportes y Métricas (Admin)
# ===========================
from flask import Blueprint, request, render_template, redirect, url_for
from flask_login import login_required, current_user
from database import get_connection

reportes_bp = Blueprint("reportes", __name__)

def _where_and_params():
    """Construye WHERE + params según filtros GET."""
    where = []
    params = []

    fecha_desde = request.args.get("desde")
    fecha_hasta = request.args.get("hasta")
    edificio = request.args.get("edificio")
    tipo_sala = request.args.get("tipo_sala")  # Libre / Posgrado / Docente

    if fecha_desde:
        where.append("r.fecha >= %s")
        params.append(fecha_desde)
    if fecha_hasta:
        where.append("r.fecha <= %s")
        params.append(fecha_hasta)
    if edificio and edificio != "todos":
        where.append("r.edificio = %s")
        params.append(edificio)
    if tipo_sala and tipo_sala != "todas":
        where.append("s.tipo_sala = %s")
        params.append(tipo_sala)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    return where_sql, tuple(params)

@reportes_bp.route("/admin/reportes", methods=["GET"])
@login_required
def admin_reportes():

    if current_user.email != "administrativo@ucu.edu.uy":
        return redirect(url_for("home"))

    conn = get_connection("reportes")
    cur = conn.cursor(dictionary=True)

    # Para combos del filtro
    cur.execute("SELECT nombre_edificio FROM edificio ORDER BY nombre_edificio;")
    edificios = [row["nombre_edificio"] for row in cur.fetchall()]
    tipos_sala = ["Libre", "Posgrado", "Docente"]

    where_sql, params = _where_and_params()

    # 1) Salas más reservadas
    cur.execute(f"""
        SELECT r.nombre_sala, r.edificio, COUNT(*) AS cantidad_reservas
        FROM reserva r
        JOIN sala s ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
        {where_sql}
        GROUP BY r.nombre_sala, r.edificio
        ORDER BY cantidad_reservas DESC
        LIMIT 10;
    """, params)
    q_salas_mas_reservadas = cur.fetchall()

    # 2) Turnos más demandados
    cur.execute(f"""
        SELECT t.hora_inicio, t.hora_fin, COUNT(*) AS reservas
        FROM reserva r
        JOIN turno t ON t.id_turno = r.id_turno
        JOIN sala s ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
        {where_sql}
        GROUP BY t.id_turno
        ORDER BY reservas DESC;
    """, params)
    q_turnos_mas_demandados = cur.fetchall()

    # 3) Promedio de participantes por sala
    cur.execute(f"""
        SELECT r.nombre_sala, r.edificio,
               ROUND(AVG(sub.cant), 2) AS promedio_participantes
        FROM (
            SELECT rp.id_reserva, COUNT(*) AS cant
            FROM reserva_participante rp
            GROUP BY rp.id_reserva
        ) sub
        JOIN reserva r ON r.id_reserva = sub.id_reserva
        JOIN sala s ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
        {where_sql}
        GROUP BY r.nombre_sala, r.edificio
        ORDER BY promedio_participantes DESC;
    """, params)
    q_prom_participantes = cur.fetchall()

    # 4) Cantidad de reservas por carrera y facultad
    cur.execute(f"""
        SELECT pa.nombre_programa,
               f.nombre AS facultad,
               COUNT(DISTINCT r.id_reserva) AS reservas
        FROM reserva r
        JOIN reserva_participante rp ON rp.id_reserva = r.id_reserva
        JOIN participantes_programa_academico ppa ON ppa.ci_participante = rp.ci_participante
        JOIN programas_academicos pa ON pa.nombre_programa = ppa.nombre_programa
        JOIN facultad f ON f.id_facultad = pa.id_facultad
        JOIN sala s ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
        {where_sql}
        GROUP BY pa.nombre_programa, f.nombre
        ORDER BY reservas DESC;
    """, params)
    q_reservas_carrera_facultad = cur.fetchall()

    # 5) % ocupación de salas por edificio (participantes / capacidad)
    cur.execute(f"""
        SELECT r.edificio,
               ROUND(
                 SUM(oc.cant_participantes) / NULLIF(SUM(s.capacidad),0) * 100, 2
               ) AS porcentaje_ocupacion
        FROM reserva r
        JOIN sala s ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
        JOIN (
            SELECT rp.id_reserva, COUNT(*) AS cant_participantes
            FROM reserva_participante rp
            GROUP BY rp.id_reserva
        ) oc ON oc.id_reserva = r.id_reserva
        {where_sql}
        GROUP BY r.edificio
        ORDER BY porcentaje_ocupacion DESC;
    """, params)
    q_ocupacion_por_edificio = cur.fetchall()

    # 6) Reservas y asistencias por rol/tipo (Docente vs Estudiante y grado/posgrado)
    cur.execute(f"""
        SELECT ppa.rol, pa.tipo,
               COUNT(DISTINCT rp.id_reserva) AS reservas,
               SUM(CASE WHEN rp.asistencia = TRUE THEN 1 ELSE 0 END) AS asistencias
        FROM reserva r
        JOIN reserva_participante rp ON rp.id_reserva = r.id_reserva
        JOIN participantes_programa_academico ppa ON ppa.ci_participante = rp.ci_participante
        JOIN programas_academicos pa ON pa.nombre_programa = ppa.nombre_programa
        JOIN sala s ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
        {where_sql}
        GROUP BY ppa.rol, pa.tipo
        ORDER BY reservas DESC;
    """, params)
    q_reservas_asistencias = cur.fetchall()

    # 7) Cantidad de sanciones por rol/tipo
    cur.execute("""
        SELECT ppa.rol, pa.tipo, COUNT(*) AS sanciones
        FROM sancion_participante sp
        JOIN participantes_programa_academico ppa ON ppa.ci_participante = sp.ci_participante
        JOIN programas_academicos pa ON pa.nombre_programa = ppa.nombre_programa
        GROUP BY ppa.rol, pa.tipo
        ORDER BY sanciones DESC;
    """)
    q_sanciones = cur.fetchall()

    # 8) % reservas utilizadas vs canceladas/no asistidas (por estado)
    cur.execute(f"""
        SELECT r.estado,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reserva r2), 2) AS porcentaje
        FROM reserva r
        JOIN sala s ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
        {where_sql.replace("WHERE", "WHERE", 1)}
        GROUP BY r.estado
        ORDER BY porcentaje DESC;
    """, params if where_sql else ())
    q_porcentaje_estado = cur.fetchall()

    # ======================
    # 3 Consultas adicionales
    # ======================

    # A) Salas con mayor tasa de cancelación (canceladas / total)
    cur.execute(f"""
        WITH tot AS (
            SELECT r.nombre_sala, r.edificio, COUNT(*) AS total
            FROM reserva r
            JOIN sala s ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
            {where_sql}
            GROUP BY r.nombre_sala, r.edificio
        ),
        canc AS (
            SELECT r.nombre_sala, r.edificio, COUNT(*) AS canceladas
            FROM reserva r
            JOIN sala s ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
            {where_sql} {" AND " if where_sql else "WHERE "} r.estado = 'Cancelada'
            GROUP BY r.nombre_sala, r.edificio
        )
        SELECT tot.nombre_sala, tot.edificio,
               ROUND(IFNULL(canc.canceladas,0)/tot.total*100,2) AS tasa_cancelacion
        FROM tot
        LEFT JOIN canc
          ON canc.nombre_sala = tot.nombre_sala AND canc.edificio = tot.edificio
        ORDER BY tasa_cancelacion DESC
        LIMIT 10;
    """, params*2 if where_sql else ())
    q_tasa_cancelacion = cur.fetchall()

    # B) Top participantes que más reservan (por confirmaciones de asistencia)
    cur.execute(f"""
        SELECT p.ci, p.nombre, p.apellido,
               COUNT(DISTINCT rp.id_reserva) AS reservas_confirmadas
        FROM reserva_participante rp
        JOIN participantes p ON p.ci = rp.ci_participante
        JOIN reserva r ON r.id_reserva = rp.id_reserva
        JOIN sala s ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
        {where_sql} {" AND " if where_sql else "WHERE "} rp.asistencia = TRUE
        GROUP BY p.ci, p.nombre, p.apellido
        ORDER BY reservas_confirmadas DESC
        LIMIT 10;
    """, params)
    q_top_participantes = cur.fetchall()

    # C) Antelación promedio de reserva (días entre solicitud y fecha)
    # Si no guardás "fecha_solicitud_reserva" en r, tomamos la de rp (está en consigna).
    cur.execute(f"""
        SELECT ROUND(AVG(DATEDIFF(r.fecha, rp.fecha_solicitud_reserva)), 2) AS antelacion_promedio_dias
        FROM reserva r
        JOIN reserva_participante rp ON rp.id_reserva = r.id_reserva
        JOIN sala s ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
        {where_sql};
    """, params)
    q_antelacion = cur.fetchone()

    conn.close()

    return render_template(
        "admin/reportes.html",
        edificios=edificios,
        tipos_sala=tipos_sala,
        # data
        q_salas_mas_reservadas=q_salas_mas_reservadas,
        q_turnos_mas_demandados=q_turnos_mas_demandados,
        q_prom_participantes=q_prom_participantes,
        q_reservas_carrera_facultad=q_reservas_carrera_facultad,
        q_ocupacion_por_edificio=q_ocupacion_por_edificio,
        q_reservas_asistencias=q_reservas_asistencias,
        q_sanciones=q_sanciones,
        q_porcentaje_estado=q_porcentaje_estado,
        q_tasa_cancelacion=q_tasa_cancelacion,
        q_top_participantes=q_top_participantes,
        q_antelacion=q_antelacion,
        # valores del filtro (para que persistan en el form)
        filtro_desde=request.args.get("desde", ""),
        filtro_hasta=request.args.get("hasta", ""),
        filtro_edificio=request.args.get("edificio", "todos"),
        filtro_tipo_sala=request.args.get("tipo_sala", "todas"),
    )
