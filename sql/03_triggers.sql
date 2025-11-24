USE ucu_reservas;

DELIMITER $$

/* =====================================================================
   TRIGGER 1 — SANCIONAR CUANDO UNA RESERVA PASA A "SIN ASISTENCIA"
   ===================================================================== */
CREATE TRIGGER trg_sancionar_por_inasistencia
AFTER UPDATE ON reserva
FOR EACH ROW
BEGIN
    IF NEW.estado = 'Sin Asistencia' AND OLD.estado <> 'Sin Asistencia' THEN

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

        INSERT INTO notificacion (ci_participante, mensaje)
        SELECT rp.ci_participante,
               CONCAT('Has sido sancionado por inasistencia en la reserva #', NEW.id_reserva)
        FROM reserva_participante rp
        WHERE rp.id_reserva = NEW.id_reserva
          AND NOT EXISTS (
              SELECT 1
              FROM sancion_participante s
              WHERE s.ci_participante = rp.ci_participante
                AND s.activa = TRUE
          );

    END IF;
END $$


/* =====================================================================
   TRIGGER 2 — CANCELAR RESERVA CUANDO TODOS SE DESCONFIRMAN
   ===================================================================== */
CREATE TRIGGER check_reserva_cancelada
AFTER UPDATE ON reserva_participante
FOR EACH ROW
BEGIN
    DECLARE restantes INT;

    IF NEW.confirmado = FALSE AND OLD.confirmado = TRUE THEN

        SELECT COUNT(*) INTO restantes
        FROM reserva_participante
        WHERE id_reserva = NEW.id_reserva
          AND confirmado = TRUE;

        IF restantes = 0 THEN
            UPDATE reserva
            SET estado = 'Cancelada'
            WHERE id_reserva = NEW.id_reserva;
        END IF;

    END IF;
END $$


/* =====================================================================
   TRIGGER 3 — MARCAR RESERVAS COMO "SIN ASISTENCIA" SI PASAN 10 MIN
   ===================================================================== */
CREATE TRIGGER trg_reservas_sin_asistencia
AFTER UPDATE ON reserva_participante
FOR EACH ROW
BEGIN
    DECLARE total_asist INT;
    DECLARE hora_fin_ultima DATETIME;
    DECLARE fecha_res DATE;
    DECLARE sala VARCHAR(100);
    DECLARE edificio VARCHAR(100);
    DECLARE turno_actual INT;

    IF NEW.asistencia <> OLD.asistencia THEN

        SELECT fecha, nombre_sala, edificio, id_turno
        INTO fecha_res, sala, edificio, turno_actual
        FROM reserva
        WHERE id_reserva = NEW.id_reserva;

        SELECT COUNT(*)
        INTO total_asist
        FROM reserva_participante rp
        JOIN reserva r ON rp.id_reserva = r.id_reserva
        WHERE r.fecha = fecha_res
          AND r.nombre_sala = sala
          AND r.edificio = edificio
          AND r.id_turno <= turno_actual
          AND rp.asistencia = TRUE;

        IF total_asist = 0 THEN

            SELECT MAX(TIMESTAMP(r.fecha, t.hora_fin))
            INTO hora_fin_ultima
            FROM reserva r
            JOIN turno t ON r.id_turno = t.id_turno
            WHERE r.fecha = fecha_res
              AND r.nombre_sala = sala
              AND r.edificio = edificio
              AND r.id_turno <= turno_actual;

            IF TIMESTAMPDIFF(MINUTE, hora_fin_ultima, NOW()) >= 10 THEN
                UPDATE reserva
                SET estado = 'Sin Asistencia'
                WHERE fecha = fecha_res
                  AND nombre_sala = sala
                  AND edificio = edificio
                  AND id_turno <= turno_actual;
            END IF;

        END IF;
    END IF;

END $$

DELIMITER ;





