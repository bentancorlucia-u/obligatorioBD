from flask import Flask, jsonify, request
from db_conexion import conexion

app = Flask(__name__)

@app.route("/")
def home():
    return "Servidor Flask conectado a la base ucu_reservas ✅"

@app.route("/reservas", methods=["GET"])
def listar_reservas():
    conexion = conexion()
    if not conexion:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reserva")
    reservas = cursor.fetchall()
    cursor.close()
    conexion.close()

    return jsonify(reservas)

@app.route("/reservas", methods=["POST"])
def crear_reserva():
    data = request.json
    connection = create_connection()
    cursor = connection.cursor()
    query = """
        INSERT INTO reserva (nombre_sala, edificio, fecha, id_turno, estado)
        VALUES (%s, %s, %s, %s, %s)
    """
    values = (data["nombre_sala"], data["edificio"], data["fecha"], data["id_turno"], "activa")
    cursor.execute(query, values)
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "✅ Reserva creada correctamente"})

if __name__ == "__main__":
    app.run(debug=True)