from werkzeug.security import check_password_hash
from flask_login import UserMixin

# toda la información necesaria de un usuario
class User(UserMixin):
    def __init__(self, ci, email, password, nombre, apellido, tipo) -> None:
        self.id = ci  # 👈 Flask-Login necesita este atributo
        self.ci = ci
        self.email = email
        self.password = password
        self.nombre = nombre
        self.apellido = apellido
        self.tipo = tipo  # grado (estudiante), posgrado (estudiante) o docente

    @classmethod
    def check_password(self, hashed_password, password):
        """Compara el hash almacenado con el password ingresado."""
        return check_password_hash(hashed_password, password)


        
