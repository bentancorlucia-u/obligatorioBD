USE ucu_reservas;

DELIMITER //

CREATE TRIGGER trg_sancionar_inasistencia
AFTER UPDATE ON reserva
FOR EACH ROW
BEGIN
    DECLARE ultima_hora_fin TIME;
    DECLARE fecha_final DATETIME;

    -- Solo aplicar si la reserva cambió a "sin asistencia"
    IF NEW.estado = 'sin asistencia' AND OLD.estado <> 'sin asistencia' THEN

        -- Recorremos cada participante que no asistió
        INSERT INTO sancion_participante (ci_participante, fecha_inicio, fecha_fin)
        SELECT rp.ci_participante, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 2 MONTH)
        FROM reserva_participante rp
        WHERE rp.id_reserva = NEW.id_reserva
          AND rp.asistencia = FALSE
          AND NOT EXISTS (
              SELECT 1 FROM sancion_participante s
              WHERE s.ci_participante = rp.ci_participante
              AND s.fecha_fin > CURDATE()
          )
          AND (
              -- Verificamos si ya pasaron 10 minutos desde el final de su última reserva consecutiva
              TIMESTAMPDIFF(
                  MINUTE,
                  (
                      SELECT MAX(TIMESTAMP(r2.fecha, t2.hora_fin))
                      FROM reserva r2
                      JOIN reserva_participante rp2 ON rp2.id_reserva = r2.id_reserva
                      JOIN turno t2 ON r2.id_turno = t2.id_turno
                      WHERE rp2.ci_participante = rp.ci_participante
                        AND r2.estado = 'sin asistencia'
                        AND r2.fecha = NEW.fecha
                        AND r2.nombre_sala = NEW.nombre_sala
                        AND r2.edificio = NEW.edificio
                        AND (
                            -- consecutivas: hora_inicio de la siguiente empieza justo donde termina la anterior
                            r2.id_turno <= NEW.id_turno
                        )
                  ),
                  NOW()
              ) >= 10
          );
    END IF;
END//

DELIMITER ;

