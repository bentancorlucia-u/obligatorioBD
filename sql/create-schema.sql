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
    estado ENUM('Activa', 'Cancelada', 'Sin Asistencia', 'Finalizada'),

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

-- indices:

ALTER TABLE reserva ADD INDEX idx_fecha_turno (fecha, id_turno);
ALTER TABLE sala ADD INDEX idx_tipo_sala (tipo_sala);






