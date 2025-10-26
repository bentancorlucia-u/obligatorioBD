-- van a ir aca los grant y revoke etc etc

-- Estos son usuarios del servidor de base de datos.
-- NO representan personas reales (ni estudiantes ni docentes).
-- Son cuentas técnicas que usan los programas o administradores para conectarse a MySQL.

USE ucu_reservas;

-- Crear usuario administrador (control total)
CREATE USER 'admin'@'localhost' IDENTIFIED BY 'admin123';

-- Crear usuario de solo lectura (para reportes o app) -> solo SELECT
CREATE USER 'lectura'@'localhost' IDENTIFIED BY 'read123';

-- Crear usuario para pruebas (acceso limitado a reservas) -> Ver e insertar reservas y participantes
CREATE USER 'reserva'@'localhost' IDENTIFIED BY 'reserva123';

-- 1. Admin: acceso completo a TOODO
GRANT ALL PRIVILEGES ON ucu_reservas.* TO 'admin'@'localhost'; -- ucu_reservas.* siginfica todas las tablas

-- 2. Lectura: solo SELECT (puede ver datos, pero no modificar)
GRANT SELECT ON ucu_reservas.* TO 'lectura'@'localhost';

-- 3. Usuario de reservas: solo puede insertar y ver reservas y participantes
GRANT SELECT, INSERT ON ucu_reservas.reserva TO 'reserva'@'localhost';
GRANT SELECT, INSERT ON ucu_reservas.reserva_participante TO 'reserva'@'localhost';
GRANT SELECT ON ucu_reservas.sala TO 'reserva'@'localhost';
GRANT SELECT ON ucu_reservas.turno TO 'reserva'@'localhost';