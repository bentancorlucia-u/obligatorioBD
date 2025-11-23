USE ucu_reservas;

DELIMITER //

/* =====================================================================
   TRIGGER 1 — SANCIONAR CUANDO UNA RESERVA PASA A "SIN ASISTENCIA"
   ---------------------------------------------------------------------
   Lógica:
   - Se ejecuta cuando cambia el estado de una reserva.
   - Si la reserva pasa a "Sin Asistencia":
       * Se sanciona a todos los participantes confirmados
         (solo si NO tienen una sanción activa).
   ===================================================================== */
DELIMITER //

CREATE TRIGGER trg_sancionar_por_inasistencia
AFTER UPDATE ON reserva
FOR EACH ROW
BEGIN
    -- Solo cuando la reserva pase a "sin asistencia"
    IF NEW.estado = 'sin asistencia' AND OLD.estado <> 'sin asistencia' THEN

        -- Insertar sanción (solo si no tiene otra activa)
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

        -- Crear notificación automática por sanción
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
END//

DELIMITER ;


/* =====================================================================
   TRIGGER 2 — CANCELAR RESERVA CUANDO TODOS LOS PARTICIPANTES SON
                 DESCONFIRMADOS
   ---------------------------------------------------------------------
   Lógica:
   - Cuando un participante actualiza su campo "confirmado".
   - Si queda 0 participantes confirmados → la reserva pasa a CANCELADA.
   ===================================================================== */
CREATE TRIGGER check_reserva_cancelada
AFTER UPDATE ON reserva_participante
FOR EACH ROW
BEGIN
    DECLARE restantes INT;

    -- Solo actuar cuando un participante se desconfirma
    IF NEW.confirmado = FALSE AND OLD.confirmado = TRUE THEN

        -- Contar cuántos siguen confirmados
        SELECT COUNT(*) INTO restantes
        FROM reserva_participante
        WHERE id_reserva = NEW.id_reserva
          AND confirmado = TRUE;

        -- Si no queda ninguno → cancelar reserva
        IF restantes = 0 THEN
            UPDATE reserva
            SET estado = 'Cancelada'
            WHERE id_reserva = NEW.id_reserva;
        END IF;

    END IF;
END//

/* =====================================================================
   TRIGGER 3 — MARCAR RESERVAS COMO "SIN ASISTENCIA" DESPUÉS DE 10 MIN
                   SI NADIE ASISTE A NINGÚN BLOQUE DEL GRUPO
   ---------------------------------------------------------------------
   Lógica:
   - Si cambia asistencia de un participante:
       * Se revisa si hay asistencia en turnos consecutivos hacia atrás.
       * Si NO hubo asistencia en ninguno:
            + Pasados 10 min del fin del bloque → marcar todo como "Sin Asistencia".
   - Este trigger es refinado y funciona por turnos secuenciales sin huecos.
   ===================================================================== */
CREATE TRIGGER trg_reservas_sin_asistencia
AFTER UPDATE ON reserva_participante
FOR EACH ROW
BEGIN
    DECLARE total_asistencias INT;
    DECLARE hora_fin_ultima DATETIME;
    DECLARE fecha_reserva DATE;
    DECLARE sala VARCHAR(100);
    DECLARE edificio VARCHAR(100);
    DECLARE turno_actual INT;

    -- Solo procesar si cambia asistencia
    IF NEW.asistencia <> OLD.asistencia THEN

        -- Obtener datos de la reserva de este registro
        SELECT fecha, nombre_sala, edificio, id_turno
        INTO fecha_reserva, sala, edificio, turno_actual
        FROM reserva
        WHERE id_reserva = NEW.id_reserva;

        -- Contar asistencia en TODAS las reservas consecutivas hacia atrás
        SELECT COUNT(*)
        INTO total_asistencias
        FROM reserva_participante rp
        JOIN reserva r ON rp.id_reserva = r.id_reserva
        WHERE r.fecha = fecha_reserva
          AND r.nombre_sala = sala
          AND r.edificio = edificio
          AND r.id_turno <= turno_actual
          AND rp.asistencia = TRUE;

        -- Si no hubo ninguna asistencia en todo el bloque consecutivo…
        IF total_asistencias = 0 THEN

            -- Buscar el fin del bloque más reciente
            SELECT MAX(TIMESTAMP(r.fecha, t.hora_fin))
            INTO hora_fin_ultima
            FROM reserva r
            JOIN turno t ON r.id_turno = t.id_turno
            WHERE r.fecha = fecha_reserva
              AND r.nombre_sala = sala
              AND r.edificio = edificio
              AND r.id_turno <= turno_actual;

            -- Si pasaron 10 minutos del final del bloque
            IF TIMESTAMPDIFF(MINUTE, hora_fin_ultima, NOW()) >= 10 THEN
                UPDATE reserva
                SET estado = 'Sin Asistencia'
                WHERE fecha = fecha_reserva
                  AND nombre_sala = sala
                  AND edificio = edificio
                  AND id_turno <= turno_actual;
            END IF;

        END IF;
    END IF;
END//

DELIMITER ;


DELIMITER //

CREATE TRIGGER trg_lista_espera_asignacion
AFTER DELETE ON reserva_participante
FOR EACH ROW
BEGIN
    DECLARE siguiente_ci CHAR(8);

    -- obtener siguiente en lista
    SELECT ci_participante INTO siguiente_ci
    FROM lista_espera
    WHERE id_reserva = OLD.id_reserva
    ORDER BY fecha ASC
    LIMIT 1;

    IF siguiente_ci IS NOT NULL THEN
        -- agregar a la reserva
        INSERT INTO reserva_participante (ci_participante, id_reserva, fecha_solicitud_reserva)
        VALUES (siguiente_ci, OLD.id_reserva, CURDATE());

        -- sacar de lista
        DELETE FROM lista_espera
        WHERE ci_participante = siguiente_ci
          AND id_reserva = OLD.id_reserva
        LIMIT 1;

        -- notificación
        INSERT INTO notificacion (ci_participante, mensaje)
        VALUES (siguiente_ci, CONCAT('Entraste automáticamente a la reserva #', OLD.id_reserva, ' desde la lista de espera.'));
    END IF;

END//

DELIMITER ;



