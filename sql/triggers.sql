USE ucu_reservas;

DELIMITER // -- necesito cambiar el delimitador para que entienda bien!

CREATE TRIGGER validar_fecha_reserva_insert -- para que la fecha a reservar sea de hoy en adelante!
BEFORE INSERT ON reserva
FOR EACH ROW
BEGIN
    IF NEW.fecha < CURDATE() THEN -- si la fecha a ingresar es menor que la actual
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'No se puede registrar una reserva en una fecha pasada.';
    END IF;
END //

DELIMITER ;

-- También aplico la misma lógica para actualizaciones!
DELIMITER //

CREATE TRIGGER validar_fecha_reserva_update
BEFORE UPDATE ON reserva
FOR EACH ROW
BEGIN
    IF NEW.fecha < CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'No se puede modificar la reserva a una fecha anterior a hoy!';
    END IF;
END //

DELIMITER ;


-- para validar emails institucionales
DELIMITER //

CREATE TRIGGER validar_email_participante_insert
BEFORE INSERT ON participantes
FOR EACH ROW
BEGIN
    -- si NO cumple patrón de alumno ni docente, lanza error
    IF NOT (
        NEW.email REGEXP '^[A-Za-z]+\\.[A-Za-z]+@correo\\.ucu\\.edu\\.uy$'
        OR NEW.email REGEXP '^[A-Za-z]+@ucu\\.edu\\.uy$'
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Email inválido: debe ser alumno o docente UCU';
    END IF;
END //

DELIMITER ;

DELIMITER //

CREATE TRIGGER validar_email_participante_update
BEFORE UPDATE ON participantes
FOR EACH ROW
BEGIN
    -- si NO cumple patrón de alumno ni docente, lanza error
    IF NOT (
        NEW.email REGEXP '^[A-Za-z]+\\.[A-Za-z]+@correo\\.ucu\\.edu\\.uy$'
        OR NEW.email REGEXP '^[A-Za-z]+@ucu\\.edu\\.uy$'
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Email inválido: debe ser alumno o docente UCU';
    END IF;
END //

DELIMITER ;

-- validar cedulas

DELIMITER //

CREATE TRIGGER validar_cedula_insert
BEFORE INSERT ON participantes
FOR EACH ROW
BEGIN
    IF NEW.ci NOT REGEXP '^[0-9]{7,8}$' THEN
        SIGNAL SQLSTATE '45000' -- lanza un error y bloquea la inserción si no cumple el patrón.
        SET MESSAGE_TEXT = 'La cédula debe tener 7 u 8 dígitos numéricos.';
    END IF;
END //

DELIMITER ;

DELIMITER //

CREATE TRIGGER validar_cedula_update
BEFORE UPDATE ON participantes
FOR EACH ROW
BEGIN
    IF NEW.ci NOT REGEXP '^[0-9]{7,8}$' THEN
        SIGNAL SQLSTATE '45000' -- lanza un error y bloquea la inserción si no cumple el patrón.
        SET MESSAGE_TEXT = 'La cédula debe tener 7 u 8 dígitos numéricos.';
    END IF;
END //

DELIMITER ;

-- validar contraseña

DELIMITER //

CREATE TRIGGER validar_password_insert
BEFORE INSERT ON login
FOR EACH ROW
BEGIN
    IF NEW.password NOT REGEXP '^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^a-zA-Z0-9]).{8,}$' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Contraseña inválida: debe tener al menos 8 caracteres, incluir mayúsculas, minúsculas, números y al menos un carácter especial.';
    END IF;
END //

DELIMITER ;

DELIMITER //

CREATE TRIGGER validar_password_update
BEFORE UPDATE ON login
FOR EACH ROW
BEGIN
    IF NEW.password NOT REGEXP '^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^a-zA-Z0-9]).{8,}$' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Contraseña inválida: debe tener al menos 8 caracteres, incluir mayúsculas, minúsculas, números y al menos un carácter especial.';
    END IF;
END //

DELIMITER ;

-- reservas diarias

DELIMITER //

CREATE TRIGGER limitar_reservas_diarias
BEFORE INSERT ON reserva_participante
FOR EACH ROW
BEGIN
    DECLARE v_tipo_sala ENUM('Libre', 'Posgrado', 'Docente');
    DECLARE v_rol ENUM('Estudiante', 'Docente');
    DECLARE v_tipo_programa ENUM('Grado', 'Posgrado');
    DECLARE v_cant INT;

    -- obtener tipo de sala
    SELECT s.tipo_sala
      INTO v_tipo_sala
      FROM reserva r
      JOIN sala s
        ON r.nombre_sala = s.nombre_sala AND r.edificio = s.edificio
     WHERE r.id_reserva = NEW.id_reserva;

    -- obtener rol y tipo de programa del participante
    SELECT ppa.rol, pa.tipo
      INTO v_rol, v_tipo_programa
      FROM participantes_programa_academico ppa
      JOIN programas_academicos pa
        ON ppa.nombre_programa = pa.nombre_programa
     WHERE ppa.ci_participante = NEW.ci_participante
     LIMIT 1;

    -- contar reservas activas del mismo día
    SELECT COUNT(*)
      INTO v_cant
      FROM reserva_participante rp
      JOIN reserva r
        ON rp.id_reserva = r.id_reserva
     WHERE rp.ci_participante = NEW.ci_participante
       AND r.fecha = (SELECT fecha FROM reserva WHERE id_reserva = NEW.id_reserva)
       AND r.estado = 'Activa';

    -- validar límite solo si aplica
    IF (v_tipo_sala = 'Libre' AND v_rol = 'Estudiante' AND v_tipo_programa = 'Grado' AND v_cant >= 2) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'El participante no puede reservar más de 2 horas diarias en salas libres.';
    END IF;
END //

DELIMITER ;

-- reservas semanales

DELIMITER //

CREATE TRIGGER limitar_reservas_semanales
BEFORE INSERT ON reserva_participante
FOR EACH ROW -- se ejecuta una vez por cada fila que se intente insertar. Si alguien hace un INSERT INTO reserva_participante ..., este trigger “intercepta” la operación y revisa las condiciones.
BEGIN -- BEGIN marca el comienzo de un bloque lógico que puede contener varias sentencias SQL

    -- Declaración de variables:
    DECLARE v_tipo_sala ENUM('Libre', 'Posgrado', 'Docente');
    DECLARE v_rol ENUM('Estudiante', 'Docente');
    DECLARE v_tipo_programa ENUM('Grado', 'Posgrado');
    DECLARE v_cant INT;
    DECLARE v_fecha DATE;

    -- obtener los datos de la reserva actual: consultar información adicional sobre ella (la fecha y el tipo de sala) que el trigger necesita para aplicar las reglas de negocio.
    -- Usa el id_reserva de la nueva fila que se quiere insertar (NEW.id_reserva).
    -- Busca en las tablas reserva y sala los datos asociados: la fecha de la reserva y el tipo de sala.
    -- Guarda esos valores en las variables v_fecha y v_tipo_sala.

    SELECT r.fecha, s.tipo_sala
      INTO v_fecha, v_tipo_sala -- guarda los valores en las variables!
      FROM reserva r
      JOIN sala s
        ON r.nombre_sala = s.nombre_sala AND r.edificio = s.edificio
     WHERE r.id_reserva = NEW.id_reserva; -- el id_reserva ya debia existir en reservas

    -- Obtener datos del participante: Toma el ci_participante del nuevo registro.
    -- Busca su rol y tipo de programa (por ejemplo: “Estudiante” de “Grado”).
    -- Guarda esos valores en las variables v_rol y v_tipo_programa.

    SELECT ppa.rol, pa.tipo  -- docente alumno || posgrado grado
      INTO v_rol, v_tipo_programa
      FROM participantes_programa_academico ppa
      JOIN programas_academicos pa
        ON ppa.nombre_programa = pa.nombre_programa
     WHERE ppa.ci_participante = NEW.ci_participante -- info que tengo del participante
     LIMIT 1;

    -- Contar cuántas reservas activas tiene esa persona en la semana
    -- Se cuentan todas las reservas activas (r.estado = 'Activa') que ese mismo participante (rp.ci_participante) tiene en la misma semana que la nueva reserva.
    SELECT COUNT(*)
      INTO v_cant -- lo guarda en la variable v_cant
      FROM reserva_participante rp
      JOIN reserva r ON rp.id_reserva = r.id_reserva
     WHERE rp.ci_participante = NEW.ci_participante -- compara por cedula
       AND YEARWEEK(r.fecha, 1) = YEARWEEK(v_fecha, 1) -- misma semana! YEARWEEK(r.fecha, 1) obtiene el número de semana del año (ISO estándar).
       AND r.estado = 'Activa';

    -- validar regla del negocio:

    IF (v_tipo_sala = 'Libre' AND v_rol = 'Estudiante' AND v_tipo_programa = 'Grado' AND v_cant >= 3) THEN
        SIGNAL SQLSTATE '45000' -- SIGNAL SQLSTATE '45000' → interrumpe la inserción y muestra el mensaje de error personalizado.
        SET MESSAGE_TEXT = 'El participante no puede tener más de 3 reservas activas en la misma semana.';
    END IF;
END //
DELIMITER ;