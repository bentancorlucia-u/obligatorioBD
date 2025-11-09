from models.entities.reserva import Reserva
from datetime import date, timedelta, datetime, time
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
                    t.hora_inicio, t.hora_fin, r.estado
                FROM reserva r
                INNER JOIN reserva_participante rp 
                    ON r.id_reserva = rp.id_reserva
                INNER JOIN turno t 
                    ON r.id_turno = t.id_turno
                WHERE rp.ci_participante = %s
                AND r.estado = 'Activa'
                ORDER BY r.fecha DESC;
            """
            cursor.execute(query, (ci,))
            reservas = cursor.fetchall()

            if not reservas:
                flash("No tenés reservas activas.", "info")

            return reservas

        except Exception as e:
            flash(f"Error al obtener reservas: {e}", "error")
            return []
    
    @classmethod
    def cancelar_reserva(cls, db, reserva: Reserva):
        """Actualiza el estado en la base de datos."""
        cursor = db.cursor()
        cursor.execute("""
            UPDATE reserva
            SET estado = %s
            WHERE id_reserva = %s AND estado = 'activa';
        """, (reserva.estado, reserva.id_reserva))
        db.commit()
        return cursor.rowcount > 0
    
    @classmethod
    def obtener_participantes(cls, db, id_reserva):
        """Trae los participantes de una reserva."""
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.ci, p.nombre, p.apellido, rp.asistencia
            FROM reserva_participante rp
            JOIN participante p ON p.ci = rp.ci_participante
            WHERE rp.id_reserva = %s;
        """, (id_reserva,))
        return cursor.fetchall()