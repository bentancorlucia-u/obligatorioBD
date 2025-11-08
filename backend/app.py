from flask import Flask, request, render_template, redirect, url_for, flash
from database import get_connection
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models.modelUser import modelUser
from models.entities.user import User
import os
from dotenv import load_dotenv

# Cargar las variables del archivo .env
load_dotenv()

# ==================================================
# CONFIGURACIÓN BASE
# ==================================================
app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/css")
app.secret_key = os.getenv("DB_SECRET_KEY")  # Necesario para sesiones y flash()

# Inicializar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Si no hay sesión, redirige acá


# ==================================================
# FUNCIÓN PARA CARGAR USUARIO POR ID
# ==================================================
@login_manager.user_loader
def load_user(user_id):
    """Flask-Login usa esta función para mantener la sesión."""
    conn = get_connection("login")
    user_data = modelUser.get_by_id(conn, user_id)
    return user_data  # Debe devolver un objeto User o None


# ==================================================
# RUTAS
# ==================================================
@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User(0, request.form["email"], request.form["password"], "", "", "")
        conn = get_connection("login")  # crear conexión por request
        logged_user = modelUser.login(conn, user)

        if logged_user is not None:
            if logged_user.password:  # contraseña correcta
                login_user(logged_user)
                return redirect(url_for("home"))
            else:
                flash("Contraseña incorrecta")
        else:
            flash("Usuario no encontrado")

        return render_template("login.html")
    else:
        return render_template("login.html")


@app.route("/home")
@login_required  # protege la ruta
def home():
    return render_template("home.html", usuario=current_user)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.")
    return redirect(url_for("login"))


# ==================================================
# MAIN
# ==================================================
if __name__ == "__main__":
    app.run(debug=True)
