from .entities.user import User
from mysql.connector import Error
from werkzeug.security import check_password_hash


class modelUser:
    @classmethod
    def login(self, db, user):
        try:
            cursor = db.cursor(dictionary=True)

            sql = """
                SELECT l.password, p.ci, p.email, p.nombre, p.apellido,
                    COALESCE(
                        CASE
                            WHEN ppa.rol = 'Docente' THEN 'Docente'
                            WHEN ppa.rol = 'Estudiante' AND pa.tipo = 'Grado' THEN 'Estudiante de grado'
                            WHEN ppa.rol = 'Estudiante' AND pa.tipo = 'Posgrado' THEN 'Estudiante de posgrado'
                            ELSE NULL
                        END,
                        'Administrativo'
                    ) AS tipo
                FROM login l
                JOIN participantes p ON l.email = p.email
                LEFT JOIN participantes_programa_academico ppa ON p.ci = ppa.ci_participante
                LEFT JOIN programas_academicos pa ON ppa.nombre_programa = pa.nombre_programa
                WHERE l.email = %s;
            """
            cursor.execute(sql, (user.email,))
            row = cursor.fetchone()

            cursor.close()
            db.close()

            if row:
                password_ok = (
                    check_password_hash(row["password"], user.password)
                    or row["password"] == user.password  # temporalmente por si no está hasheada
                )
                if password_ok:
                    return User(
                        row["ci"],
                        row["email"],
                        True,
                        row["nombre"],
                        row["apellido"],
                        row["tipo"]
                    )
            return None

        except Error as ex:
            raise Exception("Error al buscar el usuario: " + str(ex))

    @classmethod
    def get_by_id(self, db, user_ci):
        try:
            cursor = db.cursor(dictionary=True)
            sql = """
                SELECT p.ci, p.email, p.nombre, p.apellido,
                    COALESCE(
                        CASE
                            WHEN ppa.rol = 'Docente' THEN 'Docente'
                            WHEN ppa.rol = 'Estudiante' AND pa.tipo = 'Grado' THEN 'Estudiante de grado'
                            WHEN ppa.rol = 'Estudiante' AND pa.tipo = 'Posgrado' THEN 'Estudiante de posgrado'
                            ELSE NULL
                        END,
                        'Administrativo'
                    ) AS tipo
                FROM participantes p
                LEFT JOIN participantes_programa_academico ppa ON p.ci = ppa.ci_participante
                LEFT JOIN programas_academicos pa ON ppa.nombre_programa = pa.nombre_programa
                WHERE p.ci = %s;
            """
            cursor.execute(sql, (user_ci,))
            row = cursor.fetchone()

            cursor.close()
            db.close()

            if row:
                return User(
                    row["ci"],
                    row["email"],
                    None,
                    row["nombre"],
                    row["apellido"],
                    row["tipo"]
                )
            return None

        except Error as ex:
            raise Exception("Error al buscar el usuario: " + str(ex))