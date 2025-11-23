USE ucu_reservas;

DELIMITER //

CREATE EVENT ev_actualizar_estado_reservas
ON SCHEDULE EVERY 5 MINUTE
DO
BEGIN
    -- ==================================================
    -- 1) FINALIZAR reservas con asistencia
    -- ==================================================
    UPDATE reserva r
    JOIN turno t ON t.id_turno = r.id_turno
    SET r.estado = 'finalizada'
    WHERE r.estado = 'activa'
      AND TIMESTAMP(r.fecha, t.hora_fin) <= NOW()
      AND EXISTS (
          SELECT 1 # al menos un participante con asistencia = TRUE.
          FROM reserva_participante rp
          WHERE rp.id_reserva = r.id_reserva
            AND rp.asistencia = TRUE
      );

    -- ==================================================
    -- 2) MARCAR BLOQUES SIN ASISTENCIA (CONSECUTIVOS = sin huecos)
    -- ==================================================

    # Detección de “bloques” de reservas consecutivas en una misma sala/fecha
    # Si en toodo ese bloque nadie asistió y ya pasaron 10 minutos desde que terminó, se marcan todas como sin asistencia.

    WITH reservas_ordenadas AS (
        SELECT
            r.id_reserva,
            r.fecha,
            r.nombre_sala,
            r.edificio,
            r.id_turno,
            t.hora_inicio,
            t.hora_fin,
            CASE
                WHEN LAG(t.hora_fin) OVER( # mirar la reserva anterior dentro de esa sala/fecha.
                    PARTITION BY r.fecha, r.nombre_sala, r.edificio ORDER BY t.hora_inicio
                ) = t.hora_inicio THEN 0 # Si la hora_fin de la anterior coincide exactamente con la hora_inicio de la actual --> siguen pegadas, entonces NO comienza un nuevo bloque.
                ELSE 1
            END AS comienza_bloque
        FROM reserva r
        JOIN turno t ON t.id_turno = r.id_turno
        WHERE r.estado = 'activa'
    ),

    # Toma reservas_ordenadas y hace una suma acumulada de comienza_bloque
    # Esa suma acumulada genera un bloque_id
    # Mismo bloque_id = pertenecen al mismo bloque de reservas consecutivas.

    bloques AS (
        SELECT *,
               SUM(comienza_bloque) OVER(
                   PARTITION BY fecha, nombre_sala, edificio
                   ORDER BY hora_inicio
               ) AS bloque_id
        FROM reservas_ordenadas
    ),

    # Por cada bloque de reservas consecutivas, calcula:
        # fin_bloque: el fin máximo del bloque (la última hora_fin del bloque).
        # total_asistencias: cuántas reservas dentro del bloque tuvieron al menos un participante con asistencia = TRUE.
    resumen_bloques AS (
        SELECT
            fecha,
            nombre_sala,
            edificio,
            bloque_id,
            MAX(TIMESTAMP(fecha, hora_fin)) AS fin_bloque,
            SUM(CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM reserva_participante rp
                        WHERE rp.id_reserva = b.id_reserva
                          AND rp.asistencia = TRUE
                    ) THEN 1 ELSE 0
                END) AS total_asistencias
        FROM bloques b
        GROUP BY fecha, nombre_sala, edificio, bloque_id
    )

    # UPDATE FINAL
    # Toma todas las reservas activas de esos bloques donde nadie asistió en el bloque completo (total_asistencias = 0) y ya pasó al menos 10 minutos desde que terminó el bloque (fin_bloque <= NOW() - 10min)


    UPDATE reserva r
    JOIN bloques b
         ON b.id_reserva = r.id_reserva
    JOIN resumen_bloques rb
         ON rb.fecha = b.fecha
        AND rb.nombre_sala = b.nombre_sala
        AND rb.edificio = b.edificio
        AND rb.bloque_id = b.bloque_id
    SET r.estado = 'sin asistencia'
    WHERE r.estado = 'activa'
      AND rb.total_asistencias = 0
      AND rb.fin_bloque <= NOW() - INTERVAL 10 MINUTE;

END//

DELIMITER ;


CREATE EVENT actualizar_sanciones_expiradas
ON SCHEDULE EVERY 1 DAY
DO
    UPDATE sancion_participante
    SET activa = FALSE
    WHERE fecha_fin < CURDATE();

SET GLOBAL event_scheduler = ON;
