USE ucu_reservas;

DELIMITER //

/* =====================================================================
   EVENTO 1 — DESACTIVAR SANCIONES EXPIRADAS
   ---------------------------------------------------------------------
   Corre 1 vez al día.
   Pone activa = FALSE cuando la sanción ya venció.
   ===================================================================== */
CREATE EVENT ev_sanciones_expiradas
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO
    UPDATE sancion_participante
    SET activa = FALSE
    WHERE fecha_fin < CURDATE();
//

/* =====================================================================
   EVENTO 2 — ACTUALIZAR ESTADO DE RESERVAS CADA 5 MINUTOS
                (BLOQUES CONSECUTIVOS Y ASISTENCIA)
   ---------------------------------------------------------------------
   Etapas:
   1) Finalizar reservas con asistencia cuando ya terminó el turno.
   2) Identificar bloques consecutivos verdaderos.
   3) Marcar bloques completos como "Sin Asistencia" si:
        - No hubo asistencia en ninguna reserva del bloque
        - Pasaron 10 minutos desde que terminó
   ===================================================================== */
CREATE EVENT ev_actualizar_estado_reservas
ON SCHEDULE EVERY 5 MINUTE
STARTS CURRENT_TIMESTAMP
DO
BEGIN
    /* --- 1) Finalizar reservas con asistencia --- */
    UPDATE reserva r
    JOIN turno t ON t.id_turno = r.id_turno
    SET r.estado = 'Finalizada'
    WHERE r.estado = 'Activa'
      AND TIMESTAMP(r.fecha, t.hora_fin) <= NOW()
      AND EXISTS (
            SELECT 1 FROM reserva_participante rp
            WHERE rp.id_reserva = r.id_reserva
              AND rp.asistencia = TRUE
      );

    /* --- 2) Identificar bloques consecutivos sin huecos --- */
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
                WHEN LAG(t.hora_fin) OVER (
                    PARTITION BY r.fecha, r.nombre_sala, r.edificio
                    ORDER BY t.hora_inicio
                ) = t.hora_inicio THEN 0
                ELSE 1
            END AS comienza_bloque
        FROM reserva r
        JOIN turno t ON t.id_turno = r.id_turno
        WHERE r.estado = 'Activa'
    ),
    bloques AS (
        SELECT *,
               SUM(comienza_bloque) OVER(
                   PARTITION BY fecha, nombre_sala, edificio
                   ORDER BY hora_inicio
               ) AS bloque_id
        FROM reservas_ordenadas
    ),
    resumen_bloques AS (
        SELECT
            fecha,
            nombre_sala,
            edificio,
            bloque_id,
            MAX(TIMESTAMP(fecha, hora_fin)) AS fin_bloque,
            SUM(CASE
                    WHEN EXISTS (
                        SELECT 1 FROM reserva_participante rp
                        WHERE rp.id_reserva = b.id_reserva
                          AND rp.asistencia = TRUE
                    )
                THEN 1 ELSE 0 END) AS total_asistencias
        FROM bloques b
        GROUP BY fecha, nombre_sala, edificio, bloque_id
    )

    /* --- 3) Marcar "Sin Asistencia" --- */
    UPDATE reserva r
    JOIN bloques b ON b.id_reserva = r.id_reserva
    JOIN resumen_bloques rb
         ON rb.fecha = b.fecha
        AND rb.nombre_sala = b.nombre_sala
        AND rb.edificio = b.edificio
        AND rb.bloque_id = b.bloque_id
    SET r.estado = 'Sin Asistencia'
    WHERE r.estado = 'Activa'
      AND rb.total_asistencias = 0
      AND rb.fin_bloque <= NOW() - INTERVAL 10 MINUTE;

END//

/* =====================================================================
   EVENTO 3 — CONTROL GENERAL DE INASISTENCIAS CADA 5 MINUTOS
   ---------------------------------------------------------------------
   Funciones:
   - Cambiar reservas vencidas a "Finalizada" o "Sin Asistencia".
   - Sancionar automáticamente si nadie asistió (evita casos aislados).
   Este evento complementa a los triggers.
   ===================================================================== */
CREATE EVENT ev_control_inasistencias
ON SCHEDULE EVERY 5 MINUTE
STARTS CURRENT_TIMESTAMP
DO
BEGIN
  /* --- Actualizar estado de reservas vencidas --- */
  UPDATE reserva r
  JOIN turno t ON r.id_turno = t.id_turno
  SET r.estado =
      CASE
          WHEN EXISTS (
              SELECT 1 FROM reserva_participante rp
              WHERE rp.id_reserva = r.id_reserva
                AND rp.asistencia = TRUE
          ) THEN 'Finalizada'
          ELSE 'Sin Asistencia'
      END
  WHERE r.estado = 'Activa'
    AND TIMESTAMP(r.fecha, t.hora_fin) < DATE_SUB(NOW(), INTERVAL 10 MINUTE);

  /* --- Sancionar participantes si nadie asistió --- */
  INSERT INTO sancion_participante (ci_participante, fecha_inicio, fecha_fin)
  SELECT DISTINCT
      rp.ci_participante,
      CURDATE(),
      DATE_ADD(CURDATE(), INTERVAL 2 MONTH)
  FROM reserva_participante rp
  JOIN reserva r ON r.id_reserva = rp.id_reserva
  WHERE r.estado = 'Sin Asistencia'
    AND NOT EXISTS (
        SELECT 1 FROM sancion_participante s
        WHERE s.ci_participante = rp.ci_participante
          AND CURDATE() BETWEEN s.fecha_inicio AND s.fecha_fin
    );
END//

DELIMITER ;

