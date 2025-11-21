-- para actualizar el estado de las reservas
USE ucu_reservas;

DELIMITER //

CREATE EVENT ev_actualizar_estado_reservas
ON SCHEDULE EVERY 1 HOUR
DO
BEGIN
    -- Finalizar reservas pasadas CON asistencia
    UPDATE reserva r
    SET r.estado = 'finalizada'
    WHERE r.estado = 'activa'
      AND (
          r.fecha < CURDATE()
          OR (r.fecha = CURDATE() AND
              (SELECT hora_fin FROM turno WHERE id_turno = r.id_turno) < CURTIME())
      )
      AND EXISTS (
          SELECT 1
          FROM reserva_participante rp
          WHERE rp.id_reserva = r.id_reserva
          AND rp.asistencia = TRUE
      );

    -- Marcar SIN ASISTENCIA las reservas pasadas SIN asistentes
    UPDATE reserva r
    SET r.estado = 'sin asistencia'
    WHERE r.estado = 'activa'
      AND (
          r.fecha < CURDATE()
          OR (r.fecha = CURDATE() AND
              (SELECT hora_fin FROM turno WHERE id_turno = r.id_turno) < CURTIME())
      )
      AND NOT EXISTS (
          SELECT 1
          FROM reserva_participante rp
          WHERE rp.id_reserva = r.id_reserva
          AND rp.asistencia = TRUE
      );

    -- No toca las reservas canceladas (se mantienen)
END//

DELIMITER ;

CREATE EVENT actualizar_sanciones_expiradas
ON SCHEDULE EVERY 1 DAY
DO
    UPDATE sancion_participante
    SET activa = FALSE
    WHERE fecha_fin < CURDATE();

SET GLOBAL event_scheduler = ON;
