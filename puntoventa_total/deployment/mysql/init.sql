-- Inicializacion del contenedor MySQL para puntoventa_total
-- (se ejecuta la primera vez que se levanta el volumen)

CREATE DATABASE IF NOT EXISTS puntoventa
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- usuario de la aplicacion (el usuario ya viene creado por MYSQL_USER)
GRANT ALL PRIVILEGES ON puntoventa.* TO 'puntoventa'@'%';
FLUSH PRIVILEGES;

-- zonas horarias utiles para reportes
SET GLOBAL time_zone = '-05:00';

