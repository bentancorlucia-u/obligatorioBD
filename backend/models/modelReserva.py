from models.entities.reserva import Reserva
from datetime import date, timedelta
from flask import flash
from flask_login import current_user

class modelReserva:
    @classmethod
    def crear_reserva(cls, db, reserva):
        try:
            cursor = db.cursor(dictionary=True)

            # Validar fecha
            fecha_reserva = date.fromisoformat(str(reserva.fecha))
            if fecha_reserva < date.today():
                flash("No se puede crear una reserva con fecha pasada.", "error")
                return False

            # Validar turno libre
            cursor.execute("""
                SELECT COUNT(*) AS ocupadas
                FROM reserva
                WHERE nombre_sala = %s AND edificio = %s AND fecha = %s AND id_turno = %s AND estado = 'activa';
            """, (reserva.nombre_sala, reserva.edificio, reserva.fecha, reserva.id_turno))
            if cursor.fetchone()["ocupadas"] > 0:
                flash("La sala ya está reservada en ese turno", "warning")
                return False

            # Validar límite diario (solo grado)
            if "grado" in current_user.tipo.lower():
                cursor.execute("""
                    SELECT COUNT(*) AS bloques
                    FROM reserva_participante rp
                    JOIN reserva r ON rp.id_reserva = r.id_reserva
                    WHERE rp.ci_participante = %s AND r.fecha = %s AND r.estado = 'activa';
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
                      AND r.estado = 'activa';
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
            flash("Reserva creada correctamente.", "success")
            return True

        except Exception as ex:
            db.rollback()
            flash(f"Error al crear reserva: {ex}", "error")
            return False


    @classmethod
    def obtener_reservas_por_usuario(cls, db, ci_participante):
        try:
            cursor = db.cursor(dictionary=True)
            query = """
                SELECT r.*, t.hora_inicio, t.hora_fin
                FROM reserva r
                JOIN reserva_participante rp ON r.id_reserva = rp.id_reserva
                JOIN turno t ON r.id_turno = t.id_turno
                WHERE rp.ci_participante = %s
                ORDER BY r.fecha DESC;
            """
            cursor.execute(query, (ci_participante,))
            rows = cursor.fetchall()

            reservas = []
            for row in rows:
                reservas.append(
                    Reserva(
                        row["id_reserva"],
                        row["nombre_sala"],
                        row["edificio"],
                        row["fecha"],
                        row["id_turno"],
                        row["estado"],
                        hora_inicio=row["hora_inicio"],
                        hora_fin=row["hora_fin"]
                    )
                )
            return reservas
        except Exception as ex:
            flash(f"Error al obtener reservas: {f}", "error")
            return []