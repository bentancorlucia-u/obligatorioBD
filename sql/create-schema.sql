DROP DATABASE IF EXISTS ucu_reservas;
CREATE DATABASE ucu_reservas
    DEFAULT CHARACTER SET utf8
    COLLATE utf8_spanish_ci;

USE ucu_reservas;

-- ==========================================================
-- PARTICIPANTES
-- ==========================================================
CREATE TABLE participantes (
    ci CHAR(8) NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    PRIMARY KEY (ci)
);

-- ==========================================================
-- LOGIN
-- ==========================================================
CREATE TABLE login (
    email VARCHAR(150) NOT NULL,
    password VARCHAR(255) NOT NULL,
    PRIMARY KEY (email),
    FOREIGN KEY (email) REFERENCES participantes(email)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- ==========================================================
-- FACULTAD
-- ==========================================================
CREATE TABLE facultad (
    id_facultad INT AUTO_INCREMENT NOT NULL,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    PRIMARY KEY (id_facultad)
);

-- ==========================================================
-- PROGRAMAS ACADÉMICOS
-- ==========================================================
CREATE TABLE programas_academicos (
    nombre_programa VARCHAR(150) NOT NULL,
    id_facultad INT NOT NULL,
    tipo ENUM('Grado', 'Posgrado') NOT NULL,

    PRIMARY KEY (nombre_programa),

    FOREIGN KEY (id_facultad) REFERENCES facultad(id_facultad)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- ==========================================================
-- PARTICIPANTES POR PROGRAMA
-- ==========================================================
CREATE TABLE participantes_programa_academico (
    id_alumno_programa INT AUTO_INCREMENT NOT NULL,
    ci_participante CHAR(8) NOT NULL,
    nombre_programa VARCHAR(150) NOT NULL,
    rol ENUM('Estudiante', 'Docente'),

    PRIMARY KEY (id_alumno_programa),

    FOREIGN KEY (ci_participante) REFERENCES participantes(ci)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    FOREIGN KEY (nombre_programa) REFERENCES programas_academicos(nombre_programa)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE INDEX idx_participante_programa ON participantes_programa_academico(nombre_programa);

-- ==========================================================
-- EDIFICIO
-- ==========================================================
CREATE TABLE edificio (
    nombre_edificio VARCHAR(100) NOT NULL,
    direccion VARCHAR(300) NOT NULL,
    departamento VARCHAR(100) NOT NULL,
    PRIMARY KEY (nombre_edificio)
);

-- ==========================================================
-- SALA
-- ==========================================================
CREATE TABLE sala (
    nombre_sala VARCHAR(50) NOT NULL,
    edificio VARCHAR(100) NOT NULL,
    capacidad SMALLINT NOT NULL,
    tipo_sala ENUM('Libre', 'Posgrado', 'Docente'),

    PRIMARY KEY (nombre_sala, edificio),

    FOREIGN KEY (edificio) REFERENCES edificio(nombre_edificio)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CHECK (capacidad > 0 AND capacidad <= 60)
);

CREATE INDEX idx_sala_edificio ON sala(edificio);
CREATE INDEX idx_sala_tipo ON sala(tipo_sala);

-- ==========================================================
-- TURNO
-- ==========================================================
CREATE TABLE turno (
    id_turno INT AUTO_INCREMENT NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    PRIMARY KEY (id_turno),
    CHECK (hora_fin > hora_inicio)
);

-- ==========================================================
-- RESERVA
-- ==========================================================
CREATE TABLE reserva (
    id_reserva INT AUTO_INCREMENT NOT NULL,
    nombre_sala VARCHAR(50) NOT NULL,
    edificio VARCHAR(100) NOT NULL,
    fecha DATE NOT NULL,
    id_turno INT NOT NULL,
    estado ENUM('Activa', 'Cancelada', 'Sin Asistencia', 'Finalizada')
        NOT NULL DEFAULT 'Activa',

    PRIMARY KEY (id_reserva),

    FOREIGN KEY (nombre_sala, edificio)
        REFERENCES sala(nombre_sala, edificio)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    FOREIGN KEY (id_turno) REFERENCES turno(id_turno)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE INDEX idx_reserva_fecha_turno ON reserva(fecha, id_turno);
CREATE INDEX idx_reserva_turno ON reserva(id_turno);
CREATE INDEX idx_reserva_sala ON reserva(nombre_sala, edificio);

-- ==========================================================
-- RESERVA - PARTICIPANTE
-- ==========================================================
CREATE TABLE reserva_participante (
    ci_participante CHAR(8) NOT NULL,
    id_reserva INT NOT NULL,
    fecha_solicitud_reserva DATE NOT NULL,
    asistencia BOOLEAN DEFAULT FALSE,
    confirmado BOOLEAN DEFAULT TRUE,

    PRIMARY KEY (ci_participante, id_reserva),

    FOREIGN KEY (ci_participante) REFERENCES participantes(ci)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    FOREIGN KEY (id_reserva) REFERENCES reserva(id_reserva)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- ==========================================================
-- SANCIONES
-- ==========================================================
CREATE TABLE sancion_participante (
    id_sancion INT AUTO_INCREMENT NOT NULL,
    ci_participante CHAR(8) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,

    PRIMARY KEY (id_sancion),

    FOREIGN KEY (ci_participante) REFERENCES participantes(ci)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CHECK (fecha_fin >= fecha_inicio)
);

CREATE INDEX idx_sancion_ci ON sancion_participante(ci_participante);



