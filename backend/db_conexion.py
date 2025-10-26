import mysql.connector
from mysql.connector import Error

def conexion():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root', # ej: root
            password='rootpassword',
            database='ucu_reservas'
        )
        if connection.is_connected():
            print("✅ Conectado a la base de datos ucu_reservas")
        return connection
    except Error as e:
        print(f"❌ Error al conectar: {e}")
        return None