# archivo que maneja la conexión con MySQL

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Cargar las variables del archivo .env
load_dotenv()

def get_connection():
    """Crea y devuelve una conexión a la base de datos MySQL."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=os.getenv("DB_PORT")
        )
        if connection.is_connected():
            print("✅ Conexión exitosa a la base de datos.")
            return connection
    except Error as e:
        print(f"❌ Error al conectar a MySQL: {e}")
        return None