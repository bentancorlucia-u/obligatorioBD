USE ucu_reservas;

-- ==========================================================
-- PARTICIPANTES (CIs verificadas, correos institucionales)
-- ==========================================================
INSERT INTO participantes(ci, nombre, apellido, email) VALUES
('48562347','Ana','Pérez','ana.perez@correo.ucu.edu.uy'),
('51238903','Luis','González','luis.gonzalez@correo.ucu.edu.uy'),
('43782512','María','Rodríguez','maria.rodriguez@correo.ucu.edu.uy'),
('40672157','Tomás','Silva','tomas.silva@correo.ucu.edu.uy'),
('53910675','Camila','Duarte','camila.duarte@correo.ucu.edu.uy'),

('29875645','José','Rodríguez','jrodriguez@ucu.edu.uy'), /* docente */
('10000014','Admin','UCU','administrativo@ucu.edu.uy');   /* admin */

-- ==========================================================
-- LOGIN
-- ==========================================================
INSERT INTO login(email, password) VALUES
('ana.perez@correo.ucu.edu.uy','AnaP1234-'),
('luis.gonzalez@correo.ucu.edu.uy','LuisG5678*'),
('maria.rodriguez@correo.ucu.edu.uy','MariaR3456+'),
('tomas.silva@correo.ucu.edu.uy','TomasS9999!'),
('camila.duarte@correo.ucu.edu.uy','CamilaD0000?'),

('jrodriguez@ucu.edu.uy','Docente123**'),
('administrativo@ucu.edu.uy','Admin1234--');

-- ==========================================================
-- FACULTADES
-- ==========================================================
INSERT INTO facultad(nombre) VALUES
('Facultad de Ingeniería y Tecnologías'),
('Facultad de Derecho y Artes Liberales'),
('Facultad de Ciencias Empresariales'),
('Facultad de Ciencias de Salud'),
('Facultad de Psicología y Bienestar Humano');


-- ==========================================================
-- PROGRAMAS ACADÉMICOS
-- ==========================================================
INSERT INTO programas_academicos(nombre_programa, id_facultad, tipo) VALUES
-- FACULTAD DE DERECHO Y ARTES LIBERALES (2)
('Abogacía',2,'Grado'),

-- FACULTAD DE PSICOLOGÍA Y BIENESTAR HUMANO (5)
('Acompañamiento Terapéutico',5,'Grado'),
('Ciencias del Comportamiento',5,'Grado'),
('Psicología',5,'Grado'),
('Psicomotricidad',5,'Grado'),
('Psicopedagogía',5,'Grado'),

-- FACULTAD DE INGENIERÍA Y TECNOLOGÍAS (1)
('Analista en Informática',1,'Grado'),
('Desarrollador de Software',1,'Grado'),
('Ingeniería Ambiental',1,'Grado'),
('Ingeniería Biomédica',1,'Grado'),
('Ingeniería Civil',1,'Grado'),
('Ingeniería en Alimentos',1,'Grado'),
('Ingeniería en Electrónica',1,'Grado'),
('Ingeniería en Informática',1,'Grado'),
('Ingeniería en Sistemas Eléctricos de Potencia',1,'Grado'),
('Ingeniería en Telecomunicaciones',1,'Grado'),
('Ingeniería Industrial',1,'Grado'),
('Ingeniería Mecánica',1,'Grado'),
('Licenciatura en Informática',1,'Grado'),
('Ingeniería en Inteligencia Artificial y Ciencias de Datos',1,'Grado'),

-- FACULTAD DE DERECHO Y ARTES LIBERALES (2)
('Arquitectura',2,'Grado'),
('Artes Escénicas',2,'Grado'),
('Artes Visuales',2,'Grado'),
('Ciencia Política',2,'Grado'),
('Comunicación',2,'Grado'),
('Comunicación y Marketing',2,'Grado'),
('Diseño',2,'Grado'),
('Educación',2,'Grado'),
('Educación Inicial',2,'Grado'),
('Filosofía',2,'Grado'),
('Sociología',2,'Grado'),
('Trabajo Social',2,'Grado'),
('Tecnicatura en Educación y Recreación',2,'Grado'),

-- FACULTAD DE CIENCIAS EMPRESARIALES (3)
('Business Analytics',3,'Grado'),
('Contador Público',3,'Grado'),
('Datos y Negocios',3,'Grado'),
('Dirección de Empresas',3,'Grado'),
('Economía',3,'Grado'),
('Finanzas',3,'Grado'),
('Gestión Humana',3,'Grado'),
('Marketing y Estrategia Comercial',3,'Grado'),
('Negocios Internacionales',3,'Grado'),
('Negocios y Economía',3,'Grado'),

-- FACULTAD DE DERECHO Y ARTES LIBERALES (2)
('Notariado',2,'Grado'),

-- FACULTAD DE CIENCIAS DE SALUD (4)
('Agronomía',4,'Grado'),
('Fisioterapia',4,'Grado'),
('Fonoaudiología',4,'Grado'),
('Licenciatura en Enfermería',4,'Grado'),
('Licenciatura en Enfermería (Profesionalización)',4,'Grado'),
('Medicina',4,'Grado'),
('Nutrición',4,'Grado'),
('Odontología',4,'Grado'),

-- POSGRADOS
('Doctorado en Ciencia Política',2,'Posgrado'),
('Doctorado en Comunicación',2,'Posgrado'),
('Doctorado en Ingeniería',1,'Posgrado'),
('Doctorado en Psicología',5,'Posgrado'),
('Especialidad Médica en Cirugía General',4,'Posgrado'),
('Especialidad Médica en Cirugía Plástica',4,'Posgrado'),
('Maestría en Administración Pública',2,'Posgrado'),
('Maestría en Atención Temprana',5,'Posgrado'),
('Maestría en Cambio Organizacional en Entornos Digitales',3,'Posgrado'),
('Maestría en Ciencia de Datos',1,'Posgrado'),
('Maestría en Ciencias de la Ingeniería',1,'Posgrado'),
('Maestría en Comunicación Organizacional',2,'Posgrado'),
('Maestría en Cuidados Paliativos',4,'Posgrado'),
('Maestría en Currículum y Aprendizaje',2,'Posgrado'),
('Maestría en Endodoncia',4,'Posgrado'),
('Maestría en Epidemiología y Salud Digital',4,'Posgrado'),
('Maestría en Fisioterapia Traumatológica',4,'Posgrado'),
('Maestría en Gestión y Salud Pública',4,'Posgrado'),
('Maestría en Humanización de la Salud',4,'Posgrado'),
('Maestría en Intervención Social y Comunitaria',2,'Posgrado'),
('Maestría en Liderazgo y Gestión Educativa',2,'Posgrado'),
('Maestría en Metodologías Activas de Enseñanza',2,'Posgrado'),
('Maestría en Neuropsicología del Desarrollo y Aprendizaje',5,'Posgrado'),
('Maestría en Nutrición',4,'Posgrado'),
('Maestría en Ortodoncia',4,'Posgrado'),
('Maestría en Periodoncia',4,'Posgrado'),
('Maestría en Políticas Públicas',2,'Posgrado'),
('Maestría en Psicología Clínica - Opción Niños y Adolescentes',5,'Posgrado'),
('Maestría en Psicología de la Salud y Deporte',5,'Posgrado'),
('Maestría en Psicología Forense y Penitenciaria',5,'Posgrado'),
('Maestría en Psicoterapia - Psicología Analítica Junguiana',5,'Posgrado'),
('Maestría en Psicoterapia Cognitiva de Adultos y Familias - Modalidad First Experience',5,'Posgrado'),
('Maestría en Psicoterapia Cognitiva de Niños y Familias - Modalidad First Experience',5,'Posgrado'),
('Maestría en Rehabilitación Oral',4,'Posgrado'),
('Maestría en Salud y PNIE - Énfasis Ciencias de la Salud o Psicoterapia Integrativa',5,'Posgrado'),
('Postgrado en Métodos, Análisis de Datos y Evaluación',2,'Posgrado'),
('Postgrado en Negociación y Gestión Efectiva de Conflictos',2,'Posgrado'),
('Diplomatura en Diabetología',4,'Posgrado'),
('Diplomatura en Manejo de Alergias e Intolerancias Alimentarias',4,'Posgrado'),
('Diplomatura en Patología Mamaria',4,'Posgrado'),
('Diploma en Cambio, Cultura y Comunicación Interna de Organizaciones',2,'Posgrado'),
('Diploma en Comunicación de las Organizaciones Públicas',2,'Posgrado'),
('Diploma en Desarrollo de Competencias para la Gestión Educativa',2,'Posgrado'),
('Diploma en Diseño y Desarrollo Curricular',2,'Posgrado'),
('Diploma en Gestión de Conflictos en el Ámbito Comunitario',2,'Posgrado'),
('Diploma en Gestión de Conflictos en el Ámbito Educativo',2,'Posgrado'),
('Diploma en Gestión de Conflictos en el Ámbito Familiar',2,'Posgrado'),
('Diploma en Gobernanza de Internet',2,'Posgrado'),
('Diploma en Innovación Educativa',2,'Posgrado'),
('Diploma en Métodos de Investigación y Análisis de Datos',2,'Posgrado'),
('Diploma en Reputación Corporativa y Sostenibilidad',2,'Posgrado');

-- ==========================================================
-- PARTICIPANTES_PROGRAMAS_ACADÉMICOS (reducidos)
-- ==========================================================
INSERT INTO participantes_programa_academico(ci_participante, nombre_programa, rol) VALUES
('48562347','Ingeniería en Informática','Estudiante'),
('51238903','Dirección de Empresas','Estudiante'),
('43782512','Psicología','Estudiante'),
('40672157','Arquitectura','Estudiante'),
('53910675','Medicina','Estudiante'),

('29875645','Maestría en Ciencia de Datos','Docente');



-- ==========================================================
-- EDIFICIOS
-- ==========================================================

INSERT INTO edificio (nombre_edificio, direccion, departamento) VALUES
('Edificio Sacré Cœur','Av. 8 de Octubre 2738 ','Montevideo'),
('Edificio Semprún','Estero Bellaco 2771','Montevideo'),
('Edificio San José', 'Av. 8 de Octubre 2733', 'Montevideo'),
('Edificio Mullin', 'Comandante Braga 2715', 'Montevideo'),
('Edificio San Ignacio', 'Cornelio Cantera 2733', 'Montevideo'),
('Edificio Athanasius', 'Gral. Urquiza 2871', 'Montevideo'),
('Edificio Madre Marta', 'Av. Garibaldi 2831', 'Montevideo'),
('Casa Xalambri', 'Cornelio Cantera 2728', 'Montevideo'),
('Campus Salto', 'Artigas 1251', 'Salto'),
('Edificio Candelaria', 'Av. Roosevelt y Florencia, parada 7 y 1/2', 'Maldonado'),
('Edificio San Fernando', 'Av. Roosevelt y Oslo, parada 7 y 1/2', 'Maldonado');


-- ==========================================================
-- SALAS
-- ==========================================================
INSERT INTO sala(nombre_sala, edificio, capacidad, tipo_sala) VALUES
('Sala A1','Edificio Sacré Cœur',40,'Libre'),
('Sala A2','Edificio Sacré Cœur',30,'Libre'),
('Sala B1','Edificio Semprún',25,'Posgrado'),
('Sala B2','Edificio Semprún',20,'Posgrado'),
('Sala C1','Edificio San José',50,'Libre'),
('Sala C2','Edificio San José',45,'Libre'),
('Sala D1','Edificio Mullin',35,'Docente'),
('Sala D2','Edificio Mullin',30,'Docente'),
('Sala E1','Edificio San Ignacio',40,'Libre'),
('Sala E2','Edificio San Ignacio',25,'Libre'),
('Sala F1','Edificio Athanasius',20,'Docente'),
('Sala F2','Edificio Athanasius',25,'Docente'),
('Sala G1','Edificio Madre Marta',30,'Libre'),
('Sala G2','Edificio Madre Marta',35,'Libre'),
('Sala H1','Casa Xalambri',15,'Docente'),
('Sala H2','Casa Xalambri',20,'Docente'),
('Sala I1','Campus Salto',25,'Libre'),
('Sala I2','Campus Salto',30,'Libre'),
('Sala J1','Edificio Candelaria',40,'Libre'),
('Sala J2','Edificio San Fernando',35,'Libre');


-- ==========================================================
-- TURNOS
-- ==========================================================
INSERT INTO turno(hora_inicio, hora_fin) VALUES
('08:00:00', '09:00:00'),
('09:00:00', '10:00:00'),
('10:00:00', '11:00:00'),
('11:00:00', '12:00:00'),
('12:00:00', '13:00:00'),
('13:00:00', '14:00:00'),
('14:00:00', '15:00:00'),
('15:00:00', '16:00:00'),
('16:00:00', '17:00:00'),
('17:00:00', '18:00:00'),
('18:00:00', '19:00:00'),
('19:00:00', '20:00:00'),
('20:00:00', '21:00:00'),
('21:00:00', '22:00:00'),
('22:00:00', '23:00:00');

-- ==========================================================
-- RESERVAS (GRUPALES Y CON CASOS DE DEFENSA)
-- ==========================================================

-- 1) Reserva con asistencia grupal
INSERT INTO reserva(nombre_sala, edificio, fecha, id_turno, estado)
VALUES ('Sala A1','Edificio Sacré Cœur','2025-11-20',1,'Activa');

-- 2) Reserva sin asistencia → generará sanciones grupales
INSERT INTO reserva(nombre_sala, edificio, fecha, id_turno, estado)
VALUES ('Sala A2','Edificio Sacré Cœur','2025-11-20',2,'Activa');

-- 3) Reserva que se cancela por desconfirmación total (trigger)
INSERT INTO reserva(nombre_sala, edificio, fecha, id_turno, estado)
VALUES ('Sala B1','Edificio Semprún','2025-11-20',1,'Activa');

-- 4–5) Bloque consecutivo sin asistencia
INSERT INTO reserva(nombre_sala, edificio, fecha, id_turno, estado)
VALUES ('Sala C1','Edificio San Ignacio','2025-11-20',1,'Activa'),
       ('Sala C1','Edificio San Ignacio','2025-11-20',2,'Activa');


-- ==========================================================
-- RESERVA - PARTICIPANTE (GRUPALES)
-- ==========================================================

-- Reserva 1: asistencia completa de grupo
INSERT INTO reserva_participante(ci_participante,id_reserva,fecha_solicitud_reserva,asistencia,confirmado) VALUES
('48562347',1,'2025-11-01',TRUE,TRUE),
('51238903',1,'2025-11-01',TRUE,TRUE),
('43782512',1,'2025-11-01',TRUE,TRUE);

-- Reserva 2: sin asistencia → sanciones automáticas
INSERT INTO reserva_participante(ci_participante,id_reserva,fecha_solicitud_Reserva,asistencia,confirmado) VALUES
('40672157',2,'2025-11-01',FALSE,TRUE),
('53910675',2,'2025-11-01',FALSE,TRUE);

-- Reserva 3: será cancelada por desconfirmación total
INSERT INTO reserva_participante(ci_participante,id_reserva,fecha_solicitud_reserva,asistencia,confirmado) VALUES
('48562347',3,'2025-11-01',TRUE,TRUE),
('51238903',3,'2025-11-01',TRUE,TRUE);

-- Reserva 4–5: bloque consecutivo sin asistencia
INSERT INTO reserva_participante(ci_participante,id_reserva,fecha_solicitud_reserva,asistencia,confirmado) VALUES
('43782512',4,'2025-11-01',FALSE,TRUE),
('40672157',4,'2025-11-01',FALSE,TRUE),
('53910675',4,'2025-11-01',FALSE,TRUE),

('43782512',5,'2025-11-01',FALSE,TRUE),
('40672157',5,'2025-11-01',FALSE,TRUE),
('53910675',5,'2025-11-01',FALSE,TRUE);


-- ==========================================================
-- SANCIONES (historial para demo)
-- ==========================================================
INSERT INTO sancion_participante(ci_participante,fecha_inicio,fecha_fin,activa)
VALUES ('51238903','2025-10-01','2025-11-01',FALSE);



