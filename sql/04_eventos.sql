USE ucu_reservas;

DELIMITER $$

-- =====================================================================
-- EVENTO 1 — DESACTIVAR SANCIONES EXPIRADAS
-- =====================================================================
CREATE EVENT ev_sanciones_expiradas
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO
BEGIN
    UPDATE sancion_participante
    SET activa = FALSE
    WHERE fecha_fin < CURDATE();
END $$


-- =====================================================================
-- EVENTO 2 — ESTADO DE RESERVAS CADA 5 MINUTOS
-- =====================================================================
CREATE EVENT ev_actualizar_estado_reservas
ON SCHEDULE EVERY 5 MINUTE
STARTS CURRENT_TIMESTAMP
DO
BEGIN

    -- 1) Finalizar reservas con asistencia
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

    -- TABLAS TEMPORALES
    DROP TEMPORARY TABLE IF EXISTS tmp_reservas;
    CREATE TEMPORARY TABLE tmp_reservas AS
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
    WHERE r.estado = 'Activa';

    DROP TEMPORARY TABLE IF EXISTS tmp_bloques;
    CREATE TEMPORARY TABLE tmp_bloques AS
    SELECT *,
           SUM(comienza_bloque) OVER(
               PARTITION BY fecha, nombre_sala, edificio ORDER BY hora_inicio
           ) AS bloque_id
    FROM tmp_reservas;

    DROP TEMPORARY TABLE IF EXISTS tmp_resumen;
    CREATE TEMPORARY TABLE tmp_resumen AS
    SELECT
        fecha,
        nombre_sala,
        edificio,
        bloque_id,
        MAX(TIMESTAMP(fecha, hora_fin)) AS fin_bloque,
        SUM(
            CASE WHEN EXISTS (
                SELECT 1
                FROM reserva_participante rp
                WHERE rp.id_reserva = b.id_reserva
                  AND rp.asistencia = TRUE
            )
            THEN 1 ELSE 0 END
        ) AS total_asistencias
    FROM tmp_bloques b
    GROUP BY fecha, nombre_sala, edificio, bloque_id;

    -- Actualizar reservas sin asistencia
    UPDATE reserva r
    JOIN tmp_bloques b ON b.id_reserva = r.id_reserva
    JOIN tmp_resumen rb
         ON rb.fecha = b.fecha
        AND rb.nombre_sala = b.nombre_sala
        AND rb.edificio = b.edificio
        AND rb.bloque_id = b.bloque_id
    SET r.estado = 'Sin Asistencia'
    WHERE r.estado = 'Activa'
      AND rb.total_asistencias = 0
      AND rb.fin_bloque <= NOW() - INTERVAL 10 MINUTE;

END $$


-- =====================================================================
-- EVENTO 3 — CONTROL GENERAL DE INASISTENCIAS
-- =====================================================================
CREATE EVENT ev_control_inasistencias
ON SCHEDULE EVERY 5 MINUTE
STARTS CURRENT_TIMESTAMP
DO
BEGIN

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

  INSERT INTO sancion_participante (ci_participante, fecha_inicio, fecha_fin)
  SELECT DISTINCT
      rp.ci_participante,
      CURDATE(),
      DATE_ADD(CURDATE(), INTERVAL 2 MONTH)
  FROM reserva_participante rp
  JOIN reserva r ON r.id_reserva = rp.id_reserva
  WHERE r.estado = 'Sin Asistencia'
    AND NOT EXISTS (
        SELECT 1
        FROM sancion_participante s
        WHERE s.ci_participante = rp.ci_participante
          AND CURDATE() BETWEEN s.fecha_inicio AND s.fecha_fin
    );

END $$

DELIMITER ;




