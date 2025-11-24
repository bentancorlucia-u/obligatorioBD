/* ============================
   1. USUARIO ROOT / ADMIN
   ============================ */
/*
Este usuario sirve solamente para:
- Crear / modificar estructura de la BD
- Crear triggers y eventos
- Administrar usuarios
NO debe usarse en la aplicación real.
*/

GRANT ALL PRIVILEGES ON ucu_reservas.* TO 'admin'@'%' WITH GRANT OPTION;

/* ============================
   2. USUARIO ADMINISTRATIVO
   ============================ */
/*
Rol: funcionario administrativo UCU
Accesos:
- ABM completo
- NO puede modificar estructura
*/

GRANT SELECT, INSERT, UPDATE, DELETE
ON ucu_reservas.*
TO 'administrativo'@'%';

/* ============================
   3. USUARIO LOGIN
   ============================ */
/*
Rol: usuario final (estudiante, docente, etc.)
Permisos:
- Puede ver edificios, salas, turnos, programas
- Puede ver reservas y sanciones (backend filtra por CI)
- Puede crear reservas
- Puede unirse/desconfirmarse
- NO puede modificar reservas ajenas
- NO puede borrar participantes
*/

-- Lecturas básicas
GRANT SELECT ON ucu_reservas.login TO 'login'@'%';
GRANT SELECT ON ucu_reservas.participantes TO 'login'@'%';
GRANT SELECT ON ucu_reservas.participantes_programa_academico TO 'login'@'%';
GRANT SELECT ON ucu_reservas.programas_academicos TO 'login'@'%';
GRANT SELECT ON ucu_reservas.sala TO 'login'@'%';
GRANT SELECT ON ucu_reservas.edificio TO 'login'@'%';
GRANT SELECT ON ucu_reservas.turno TO 'login'@'%';

-- notificaciones
GRANT INSERT, UPDATE, SELECT
ON ucu_reservas.notificacion
TO 'login'@'%';

-- Ver reservas y sanciones
GRANT SELECT ON ucu_reservas.reserva TO 'login'@'%';
GRANT SELECT ON ucu_reservas.reserva_participante TO 'login'@'%';
GRANT SELECT ON ucu_reservas.sancion_participante TO 'login'@'%';

-- Crear una reserva propia
GRANT INSERT ON ucu_reservas.reserva TO 'login'@'%';

-- Unirse / desconfirmarse (pero NO borrar)
GRANT INSERT, UPDATE ON ucu_reservas.reserva_participante TO 'login'@'%';


/*
IMPORTANTE:
NO usamos REVOKE porque el usuario login nunca recibió
UPDATE/DELETE sobre reserva, así que MySQL tiraría error.
*/


/* ============================
   4. USUARIO REPORTES
   ============================ */
/*
Rol: BI / analítica
Acceso solo lectura
*/

GRANT SELECT ON ucu_reservas.*
TO 'reportes'@'%';


/* ============================
   5. FINALIZAR
   ============================ */
FLUSH PRIVILEGES;