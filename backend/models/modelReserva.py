from models.entities.reserva import Reserva
from datetime import date, timedelta, datetime, time
from flask import flash
from flask_login import current_user

class modelReserva:
    @classmethod
    def crear_reserva(cls, db, reserva):
        try:
            cursor = db.cursor(dictionary=True)

            # Verificar si el participante está sancionado
            cursor.execute("""
                SELECT DATE_FORMAT(fecha_fin, '%d/%m/%Y') AS fin
                FROM sancion_participante
                WHERE ci_participante = %s
                AND CURDATE() BETWEEN fecha_inicio AND fecha_fin;
            """, (current_user.ci,))
            sancion = cursor.fetchone()

            if sancion:
                flash(f"No puedes crear una reserva: estás sancionado hasta el {sancion['fin']}.", "error")
                return False

            # Validar fecha
            fecha_reserva = date.fromisoformat(str(reserva.fecha))
            if fecha_reserva < date.today():
                flash("No se puede crear una reserva con fecha pasada.", "error")
                return False

           # Validar que el turno no haya pasado si la reserva es para hoy
            if fecha_reserva == date.today():
                cursor.execute("""
                    SELECT hora_inicio FROM turno WHERE id_turno = %s;
                """, (reserva.id_turno,))
                result = cursor.fetchone()

                if not result:
                    flash("⚠ No se encontró el turno seleccionado.", "error")
                    return False

                hora_actual = datetime.now().time()
                hora_turno_raw = result["hora_inicio"]

                # Convertir timedelta → time si es necesario
                if isinstance(hora_turno_raw, timedelta):
                    total_seconds = int(hora_turno_raw.total_seconds())
                    horas = total_seconds // 3600
                    minutos = (total_seconds % 3600) // 60
                    hora_turno = time(horas, minutos)
                else:
                    hora_turno = hora_turno_raw

                # Comparar correctamente
                if hora_turno < hora_actual:
                    flash("No se puede reservar un turno que ya comenzó o finalizó.", "error")
                    return False
                
            # Validar turno libre
            cursor.execute("""
                SELECT COUNT(*) AS ocupadas
                FROM reserva
                WHERE nombre_sala = %s AND edificio = %s AND fecha = %s AND id_turno = %s AND estado = 'Activa';
            """, (reserva.nombre_sala, reserva.edificio, reserva.fecha, reserva.id_turno))
            if cursor.fetchone()["ocupadas"] > 0:
                flash("La sala ya está reservada en ese turno", "warning")
                return False
            
            # validar sala y tipo de usuario

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
            usuario_tipo = cursor.fetchone()

            if not usuario_tipo:
                flash("No se pudo determinar tu tipo de usuario.", "error")
                return False

            tipo_persona = usuario_tipo["tipo_persona"]

            # Obtener tipo de sala
            cursor.execute("""
                SELECT tipo_sala
                FROM sala
                WHERE nombre_sala = %s AND edificio = %s;
            """, (reserva.nombre_sala, reserva.edificio))
            sala = cursor.fetchone()

            if not sala:
                flash("No se encontró la sala seleccionada.", "error")
                return False

            tipo_sala = sala["tipo_sala"]

            # Reglas de validación según tipo de persona
            if tipo_sala == "Docente" and tipo_persona != "Docente":
                flash("Solo los docentes pueden reservar esta sala.", "error")
                return False

            if tipo_sala == "Posgrado" and tipo_persona != "Estudiante de posgrado":
                flash("Solo los estudiantes de posgrado pueden reservar esta sala.", "error")
                return False

            # Validar límite diario (solo grado)
            if "grado" in current_user.tipo.lower():
                cursor.execute("""
                    SELECT COUNT(*) AS bloques
                    FROM reserva_participante rp
                    JOIN reserva r ON rp.id_reserva = r.id_reserva
                    WHERE rp.ci_participante = %s AND r.fecha = %s AND r.estado = 'Activa';
                """, (current_user.ci, reserva.fecha))
                if cursor.fetchone()["bloques"] >= 2:
                    flash("No puedes reservar más de 2 horas por día.", "error")
                    return False

            # Validar límite semanal (solo grado)
            if "grado" in current_user.tipo.lower():
                hoy = date.today()
                inicio_semana = hoy - timedelta(days=hoy.weekday())  # Lunes
                fin_semana = inicio_semana + timedelta(days=6)       # Domingo

                cursor.execute("""
                    SELECT COUNT(*) AS cantidad
                    FROM reserva_participante rp
                    JOIN reserva r ON rp.id_reserva = r.id_reserva
                    WHERE rp.ci_participante = %s
                      AND r.fecha BETWEEN %s AND %s
                      AND r.estado = 'Activa';
                """, (current_user.ci, inicio_semana, fin_semana))
                if cursor.fetchone()["cantidad"] >= 3:
                    flash("No puedes tener más de 3 reservas activas en la semana.", "error")
                    return False

            # Insertar la reserva
            cursor.execute("""
                INSERT INTO reserva (nombre_sala, edificio, fecha, id_turno, estado)
                VALUES (%s, %s, %s, %s, %s);
            """, (reserva.nombre_sala, reserva.edificio, reserva.fecha, reserva.id_turno, reserva.estado))
            id_reserva = cursor.lastrowid

            # Asociar usuario logueado
            cursor.execute("""
                INSERT INTO reserva_participante (ci_participante, id_reserva, fecha_solicitud_reserva)
                VALUES (%s, %s, %s);
            """, (current_user.ci, id_reserva, date.today()))

            db.commit()
            return True

        except Exception as ex:
            db.rollback()
            flash(f"Error al crear reserva: {ex}", "error")
            return False


    @classmethod
    def obtener_reservas_por_usuario(cls, db, ci):
        try:
            cursor = db.cursor(dictionary=True)
            query = """
                SELECT r.id_reserva, r.nombre_sala, r.edificio, r.fecha,
                    t.hora_inicio, t.hora_fin, r.estado,
                    s.capacidad,
                    (
                        SELECT COUNT(*) 
                        FROM reserva_participante rp2 
                        WHERE rp2.id_reserva = r.id_reserva 
                            AND rp2.confirmado = TRUE
                    ) AS participantes_confirmados
                FROM reserva r
                INNER JOIN reserva_participante rp 
                    ON r.id_reserva = rp.id_reserva
                INNER JOIN turno t 
                    ON r.id_turno = t.id_turno
                INNER JOIN sala s 
                    ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
                WHERE rp.ci_participante = %s
                AND rp.confirmado = TRUE        -- Solo reservas donde el usuario confirmó asistencia
                AND r.estado = 'Activa'         -- Solo reservas activas
                ORDER BY r.fecha DESC;
            """
            cursor.execute(query, (ci,))
            reservas = cursor.fetchall()

            # Traer otros participantes confirmados (no el usuario actual)
            for r in reservas:
                cursor.execute("""
                    SELECT CONCAT(p.nombre, ' ', p.apellido) AS nombre_completo
                    FROM reserva_participante rp
                    JOIN participantes p ON p.ci = rp.ci_participante
                    WHERE rp.id_reserva = %s 
                    AND rp.ci_participante != %s
                    AND rp.confirmado = TRUE;
                """, (r["id_reserva"], ci))
                otros = cursor.fetchall()
                r["participantes"] = [p["nombre_completo"] for p in otros]

            return reservas

        except Exception as e:
            flash(f"Error al obtener reservas: {e}", "error")
            return []