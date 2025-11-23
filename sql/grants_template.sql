/* ===========================================================
     SISTEMA DE USUARIOS Y PRIVILEGIOS — UCU_RESERVAS
     TEMPLATE SIN CONTRASEÑAS (seguro para publicación)
   =========================================================== */

/* ===========================================================
   1. USUARIO ROOT / ADMIN (uso técnico)
   -----------------------------------------------------------
   - Gestiona estructura
   - Crea triggers, eventos
   - Administra otros usuarios
   - NO se usa en la aplicación
   =========================================================== */

CREATE USER IF NOT EXISTS 'admin'@'localhost'
IDENTIFIED BY '***REEMPLAZAR_PASSWORD***';

GRANT ALL PRIVILEGES
ON ucu_reservas.*
TO 'admin'@'localhost'
WITH GRANT OPTION;


/* ===========================================================
   2. USUARIO ADMINISTRATIVO (ABM completo)
   -----------------------------------------------------------
   - Puede hacer ALTAS, BAJAS y MODIFICACIONES
   - No puede alterar estructura
   =========================================================== */

CREATE USER IF NOT EXISTS 'administrativo'@'localhost'
IDENTIFIED BY '***REEMPLAZAR_PASSWORD***';

GRANT SELECT, INSERT, UPDATE, DELETE
ON ucu_reservas.*
TO 'administrativo'@'localhost';


/* ===========================================================
   3. USUARIO LOGIN (estudiantes y docentes)
   -----------------------------------------------------------
   - Lee edificios, salas, turnos, programas
   - Ve sus reservas y sanciones (filtrado en backend)
   - Crea reservas
   - Puede unirse/desconfirmarse
   - NO puede borrar/modificar reservas ajenas
   =========================================================== */

CREATE USER IF NOT EXISTS 'login'@'localhost'
IDENTIFIED BY '***REEMPLAZAR_PASSWORD***';

/* Lecturas básicas */
GRANT SELECT ON ucu_reservas.login                         TO 'login'@'localhost';
GRANT SELECT ON ucu_reservas.participantes                 TO 'login'@'localhost';
GRANT SELECT ON ucu_reservas.participantes_programa_academico TO 'login'@'localhost';
GRANT SELECT ON ucu_reservas.programas_academicos          TO 'login'@'localhost';
GRANT SELECT ON ucu_reservas.sala                          TO 'login'@'localhost';
GRANT SELECT ON ucu_reservas.edificio                      TO 'login'@'localhost';
GRANT SELECT ON ucu_reservas.turno                         TO 'login'@'localhost';

/* Lecturas de reservas y sanciones */
GRANT SELECT ON ucu_reservas.reserva                       TO 'login'@'localhost';
GRANT SELECT ON ucu_reservas.reserva_participante          TO 'login'@'localhost';
GRANT SELECT ON ucu_reservas.sancion_participante          TO 'login'@'localhost';

/* Crear reserva propia */
GRANT INSERT ON ucu_reservas.reserva                       TO 'login'@'localhost';

/* Unirse / desconfirmarse */
GRANT INSERT, UPDATE
ON ucu_reservas.reserva_participante
TO 'login'@'localhost';


/* ===========================================================
   4. USUARIO REPORTES (solo lectura)
   -----------------------------------------------------------
   - Utilizado para BI y reportes
   =========================================================== */

CREATE USER IF NOT EXISTS 'reportes'@'localhost'
IDENTIFIED BY '***REEMPLAZAR_PASSWORD***';

GRANT SELECT
ON ucu_reservas.*
TO 'reportes'@'localhost';


/* ===========================================================
   5. APLICAR CAMBIOS
   =========================================================== */

FLUSH PRIVILEGES;
