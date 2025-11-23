USE ucu_reservas;

-- ---------------- PARTICIPANTES ----------------
INSERT INTO participantes(ci, nombre, apellido, email) VALUES
('12345678','Ana','Pérez','ana.perez@correo.ucu.edu.uy'),
('23456789','Luis','González','luis.gonzalez@correo.ucu.edu.uy'),
('34567890','María','Rodríguez','maria.rodriguez@correo.ucu.edu.uy'),
('45678901','Juan','López','juan.lopez@correo.ucu.edu.uy'),
('56789012','Sofía','Martínez','sofia.martinez@correo.ucu.edu.uy'),
('67890123','Carlos','Fernández','carlos.fernandez@correo.ucu.edu.uy'),
('78901234','Laura','Gómez','laura.gomez@correo.ucu.edu.uy'),
('89012345','Diego','Díaz','diego.diaz@correo.ucu.edu.uy'),
('90123456','Valentina','Santos','valentina.santos@correo.ucu.edu.uy'),
('11223344','Pablo','Vega','pablo.vega@correo.ucu.edu.uy'),
('22334455','Lucía','Ramos','lucia.ramos@correo.ucu.edu.uy'),
('33445566','Mateo','Castro','mateo.castro@correo.ucu.edu.uy'),
('44556677','Isabella','Pinto','isabella.pinto@correo.ucu.edu.uy'),
('55667788','Tomás','Herrera','tomas.herrera@correo.ucu.edu.uy'),
('66778899','Juliana','Silva','juliana.silva@correo.ucu.edu.uy'),
('77889900','Sebastián','Morales','sebastian.morales@correo.ucu.edu.uy'),
('88990011','Martina','Rojas','martina.rojas@correo.ucu.edu.uy'),
('99001122','Federico','Alonso','federico.alonso@correo.ucu.edu.uy'),
('10111213','Camila','Navarro','camila.navarro@correo.ucu.edu.uy');

-- ---------------- LOGIN ----------------
INSERT INTO login(email, password) VALUES
('ana.perez@correo.ucu.edu.uy','AnaP1234-'),
('luis.gonzalez@correo.ucu.edu.uy','LuisG5678*'),
('maria.rodriguez@correo.ucu.edu.uy','MariaR9012!'),
('juan.lopez@correo.ucu.edu.uy','JuanL3456$'),
('sofia.martinez@correo.ucu.edu.uy','SofiaM7890%'),
('carlos.fernandez@correo.ucu.edu.uy','CarlosF2345#'),
('laura.gomez@correo.ucu.edu.uy','LauraG6789@'),
('diego.diaz@correo.ucu.edu.uy','DiegoD0123^'),
('valentina.santos@correo.ucu.edu.uy','ValenS4567&'),
('pablo.vega@correo.ucu.edu.uy','PabloV8901*'),
('lucia.ramos@correo.ucu.edu.uy','LuciaR2345!'),
('mateo.castro@correo.ucu.edu.uy','MateoC6789-'),
('isabella.pinto@correo.ucu.edu.uy','IsabellaP0123$'),
('tomas.herrera@correo.ucu.edu.uy','TomasH4567#'),
('juliana.silva@correo.ucu.edu.uy','JulianaS8901@'),
('sebastian.morales@correo.ucu.edu.uy','SebastianM2345%'),
('martina.rojas@correo.ucu.edu.uy','MartinaR6789^'),
('federico.alonso@correo.ucu.edu.uy','FedericoA0123*'),
('camila.navarro@correo.ucu.edu.uy','CamilaN4567!');

-- ---------------- FACULTAD ----------------
INSERT INTO facultad(nombre) VALUES
('Facultad de Ingeniería y Tecnologías'),
('Facultad de Derecho y Artes Liberales'),
('Facultad de Ciencias Empresariales'),
('Facultad de Ciencias de Salud'),
('Facultad de Psicología y Bienestar Humano');


-- ---------------- PROGRAMAS ACADÉMICOS ----------------
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

-- ---------------- PARTICIPANTES_PROGRAMAS_ACADÉMICOS ----------------
INSERT INTO participantes_programa_academico(id_alumno_programa, ci_participante, nombre_programa, rol) VALUES
(1,'12345678','Abogacía','Estudiante'),
(2,'23456789','Ingeniería Civil','Estudiante'),
(3,'34567890','Psicología','Estudiante'),
(4,'45678901','Medicina','Estudiante'),
(5,'56789012','Arquitectura','Estudiante'),
(6,'67890123','Contador Público','Estudiante'),
(7,'78901234','Comunicación','Estudiante'),
(8,'89012345','Educación','Estudiante'),
(9,'90123456','Diseño','Estudiante'),
(10,'11223344','Abogacía','Estudiante'),
(11,'22334455','Ingeniería en Informática','Estudiante'),
(12,'33445566','Trabajo Social','Estudiante'),
(13,'44556677','Marketing y Estrategia Comercial','Estudiante'),
(14,'55667788','Ingeniería Mecánica','Estudiante'),
(15,'66778899','Negocios Internacionales','Estudiante'),
(16,'77889900','Licenciatura en Enfermería','Estudiante'),
(17,'88990011','Arquitectura','Docente'),
(18,'99001122','Psicomotricidad','Docente'),
(19,'10111213','Filosofía','Docente');
-- ---------------- EDIFICIO ----------------
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

-- ---------------- SALA ----------------
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


-- ---------------- TURNO ----------------
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

-- ---------------- RESERVA ----------------
INSERT INTO reserva(nombre_sala, edificio, fecha, id_turno, ESTADO) VALUES
('Sala A1','Edificio Sacré Cœur','2025-11-01',1,'Activa'),
('Sala A2','Edificio Sacré Cœur','2025-11-02',2,'Activa'),
('Sala B1','Edificio Semprún','2025-11-03',3,'Activa'),
('Sala B2','Edificio Semprún','2025-11-04',4,'Activa'),
('Sala C1','Edificio San José','2025-11-05',5,'Activa'),
('Sala C2','Edificio San José','2025-11-06',6,'Activa'),
('Sala D1','Edificio Mullin','2025-11-07',7,'Activa'),
('Sala D2','Edificio Mullin','2025-11-08',8,'Activa'),
('Sala E1','Edificio San Ignacio','2025-11-09',9,'Activa'),
('Sala E2','Edificio San Ignacio','2025-11-10',10,'Activa'),
('Sala F1','Edificio Athanasius','2025-11-11',11,'Activa'),
('Sala F2','Edificio Athanasius','2025-11-12',12,'Activa'),
('Sala G1','Edificio Madre Marta','2025-11-13',13,'Activa'),
('Sala G2','Edificio Madre Marta','2025-11-14',14,'Activa'),
('Sala H1','Casa Xalambri','2025-11-15',15,'Activa');

-- ---------------- RESERVA_PARTICIPANTE ----------------
INSERT INTO reserva_participante(ci_participante, id_reserva, fecha_solicitud_reserva, asistencia) VALUES
('12345678',1,'2025-10-24',TRUE),
('23456789',2,'2025-10-24',TRUE),
('34567890',3,'2025-10-24',FALSE),
('45678901',4,'2025-10-24',TRUE),
('56789012',5,'2025-10-24',FALSE),
('67890123',6,'2025-10-24',TRUE),
('78901234',7,'2025-10-24',TRUE),
('89012345',8,'2025-10-24',FALSE),
('90123456',9,'2025-10-24',TRUE),
('11223344',10,'2025-10-24',TRUE),
('22334455',11,'2025-10-24',FALSE),
('33445566',12,'2025-10-24',TRUE),
('44556677',13,'2025-10-24',TRUE),
('55667788',14,'2025-10-24',FALSE),
('66778899',15,'2025-10-24',TRUE);

-- ---------------- SANCION_PARTICIPANTE ----------------
INSERT INTO sancion_participante(ci_participante, fecha_inicio, fecha_fin) VALUES
('12345678','2025-10-25','2025-11-01'),
('23456789','2025-10-26','2025-11-02'),
('34567890','2025-10-27','2025-11-03'),
('45678901','2025-10-28','2025-11-04'),
('56789012','2025-10-29','2025-11-05'),
('67890123','2025-10-30','2025-11-06'),
('78901234','2025-10-31','2025-11-07'),
('89012345','2025-11-01','2025-11-08');


INSERT INTO login(email, password) VALUE
('administrativo@ucu.edu.uy', 'admin123');



