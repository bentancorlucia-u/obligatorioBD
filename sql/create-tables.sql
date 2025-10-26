DROP DATABASE IF EXISTS ucu_reservas;
CREATE DATABASE ucu_reservas DEFAULT CHARACTER SET utf8 COLLATE utf8_spanish_ci;

USE ucu_reservas;

CREATE TABLE participantes (
    ci CHAR(8) NOT NULL, -- para el formato de cedula!
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,

    PRIMARY KEY (ci)
);

CREATE TABLE login (
    email VARCHAR(150) NOT NULL,
    password VARCHAR(50) NOT NULL,
    PRIMARY KEY (email), -- no pueden haber dos emails iguales
    FOREIGN KEY (email) REFERENCES participantes(email)
);

CREATE TABLE facultad (
    id_facultad INT AUTO_INCREMENT NOT NULL,
    nombre VARCHAR(100) NOT NULL,

    PRIMARY KEY (id_facultad)
);

CREATE TABLE programas_academicos (
    nombre_programa VARCHAR(150) NOT NULL,
    id_facultad INT NOT NULL,
    tipo ENUM('Grado', 'Posgrado') NOT NULL,

    PRIMARY KEY (nombre_programa),
    FOREIGN KEY (id_facultad) REFERENCES facultad(id_facultad)

);

CREATE TABLE participantes_programa_academico (
    id_alumno_programa INT NOT NULL,
    ci_participante CHAR(8) NOT NULL,
    nombre_programa VARCHAR(150) NOT NULL,
    rol ENUM('Estudiante', 'Docente'),

    PRIMARY KEY (id_alumno_programa),
    FOREIGN KEY (ci_participante) REFERENCES participantes(ci),
    FOREIGN KEY (nombre_programa) REFERENCES programas_academicos(nombre_programa)
);

CREATE TABLE edificio (
    nombre_edificio VARCHAR(100) NOT NULL,
    direccion VARCHAR(300) NOT NULL,
    departamento VARCHAR(100) NOT NULL,

    PRIMARY KEY (nombre_edificio)
);

CREATE TABLE sala (
    nombre_sala VARCHAR(100) NOT NULL,
    edificio VARCHAR(100) NOT NULL,
    capacidad SMALLINT,
    tipo_sala ENUM('Libre', 'Posgrado', 'Docente'),

    PRIMARY KEY (nombre_sala, edificio),
    FOREIGN KEY (edificio) REFERENCES edificio(nombre_edificio)
);

CREATE TABLE turno (
    id_turno INT AUTO_INCREMENT NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,

    PRIMARY KEY (id_turno)
);

CREATE TABLE reserva (
    id_reserva INT AUTO_INCREMENT NOT NULL,
    nombre_sala VARCHAR(100) NOT NULL,
    edificio VARCHAR(100) NOT NULL,
    fecha DATE NOT NULL,
    id_turno INT NOT NULL,
    ESTADO ENUM('Activa', 'Cancelada', 'Sin Asistencia', 'Finalizada'),

    PRIMARY KEY (id_reserva),
    FOREIGN KEY (nombre_sala, edificio) REFERENCES sala(nombre_sala,edificio),
    FOREIGN KEY (id_turno) REFERENCES turno(id_turno)
);

CREATE TABLE reserva_participante (
    ci_participante CHAR(8) NOT NULL,
    id_reserva INT NOT NULL,
    fecha_solicitud_reserva DATE NOT NULL,
    asistencia BOOLEAN DEFAULT FALSE,

    PRIMARY KEY (ci_participante, id_reserva),
    FOREIGN KEY (ci_participante) REFERENCES participantes(ci),
    FOREIGN KEY (id_reserva) REFERENCES reserva(id_reserva)
);

CREATE TABLE sancion_participante (
    id_sancion INT AUTO_INCREMENT,
    ci_participante CHAR(8) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,

    PRIMARY KEY (id_sancion),
    FOREIGN KEY (ci_participante) REFERENCES participantes(ci)
);

DELIMITER // -- necesito cambiar el delimitador para que entienda bien!

CREATE TRIGGER validar_fecha_reserva_insert -- para que la fecha a reservar sea de hoy en adelante!
BEFORE INSERT ON reserva
FOR EACH ROW
BEGIN
    IF NEW.fecha < CURDATE() THEN
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




