# archivo que maneja la conexión con MySQL
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Cargar las variables del archivo .env
load_dotenv()

def get_connection(role="reportes"):
    try:
        creds = {
            "administrativo": {
                "user": os.getenv("DB_USER_ADMINISTRATIVO"),
                "password": os.getenv("DB_PASS_ADMINISTRATIVO")
            },
            "reportes": {
                "user": os.getenv("DB_USER_REPORTE"),
                "password": os.getenv("DB_PASS_REPORTE")
            },
            "login": {
                "user": os.getenv("DB_USER_LOGIN"),
                "password": os.getenv("DB_PASS_LOGIN")
            }
        }

        if role not in creds:
            raise KeyError(f"Rol '{role}' no existe en la configuración")

        user = creds[role]["user"]
        password = creds[role]["password"]

        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=user,
            password=password
        )

        if conn.is_connected():
            print(f"✅ Conectado a MySQL como {role}")
            return conn

    except KeyError as e:
        print(f"❌ {e}")
    except Error as e:
        print(f"⚠️ Error al conectar a MySQL: {e}")
    return None

