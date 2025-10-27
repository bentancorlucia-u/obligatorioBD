from flask import Flask, jsonify
from database import get_connection

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Sistema de Reservas UCU activo 🚀"})

@app.route('/test-db')
def test_db():
    connection = get_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total FROM participantes;")
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return jsonify({
            "message": "Conexión a la base de datos exitosa ✅",
            "total_participantes": result["total"]
        })
    else:
        return jsonify({"error": "No se pudo conectar a la base de datos ❌"}), 500

if __name__ == '__main__':
    app.run(debug=True)