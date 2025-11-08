from database import get_connection
from werkzeug.security import generate_password_hash

def hash_existing_passwords():
    # Conectar con un usuario que tenga permiso de UPDATE
    conn = get_connection("administrativo")  # o "admin" si preferís
    if not conn:
        print("❌ No se pudo conectar a la base de datos.")
        return

    cursor = conn.cursor(dictionary=True)

    # 1️⃣ Traer todos los usuarios con su contraseña actual
    cursor.execute("SELECT email, password FROM login;")
    usuarios = cursor.fetchall()

    for user in usuarios:
        email = user["email"]
        password = user["password"]

        # Si el password ya está hasheado (empieza con pbkdf2), lo saltamos
        if password.startswith("pbkdf2:sha256:"):
            print(f"🔹 {email} ya está hasheado. Se omite.")
            continue

        # 2️⃣ Generar hash nuevo
        hashed = generate_password_hash(password)

        # 3️⃣ Actualizar la base
        update_sql = "UPDATE login SET password = %s WHERE email = %s;"
        cursor.execute(update_sql, (hashed, email))
        print(f"✅ Contraseña actualizada para: {email}")

    # 4️⃣ Guardar cambios
    conn.commit()
    cursor.close()
    conn.close()
    print("\n🎉 Todas las contraseñas fueron actualizadas correctamente.")

if __name__ == "__main__":
    hash_existing_passwords()
