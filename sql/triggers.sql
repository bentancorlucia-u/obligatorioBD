USE ucu_reservas;

DELIMITER //

CREATE TRIGGER trg_sancionar_por_inasistencia
AFTER UPDATE ON reserva
FOR EACH ROW
BEGIN
    -- Solo cuando pasa a "sin asistencia"
    IF NEW.estado = 'sin asistencia' AND OLD.estado <> 'sin asistencia' THEN

        INSERT INTO sancion_participante (ci_participante, fecha_inicio, fecha_fin, activa)
        SELECT rp.ci_participante, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 2 MONTH), TRUE
        FROM reserva_participante rp
        WHERE rp.id_reserva = NEW.id_reserva
          AND NOT EXISTS (
                SELECT 1
                FROM sancion_participante s
                WHERE s.ci_participante = rp.ci_participante
                  AND s.activa = TRUE
          );

    END IF;
END//

DELIMITER ;



# Si un participante es "desconfirmado", y como consecuencia ningún participante queda confirmado en esa reserva, entonces la reserva se cancela automáticamente.

DELIMITER //
CREATE TRIGGER check_reserva_cancelada
AFTER UPDATE ON reserva_participante
FOR EACH ROW
BEGIN
    DECLARE restantes INT;
    IF NEW.confirmado = FALSE THEN
        SELECT COUNT(*) INTO restantes
        FROM reserva_participante
        WHERE id_reserva = NEW.id_reserva AND confirmado = TRUE;

        IF restantes = 0 THEN
            UPDATE reserva
            SET estado = 'cancelada'
            WHERE id_reserva = NEW.id_reserva;
        END IF;
    END IF;
END;
//
DELIMITER ;


