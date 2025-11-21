import re
import random
import string

# ==================================================
# GENERADOR DE CONTRASEÑAS
# ==================================================
def generar_contrasena(longitud=10):
    """Genera una contraseña aleatoria con letras y números."""
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(longitud))


# ==================================================
# VALIDACIONES DE CÉDULA Y CORREO
# ==================================================
def validar_cedula_uruguaya(cedula: str) -> bool:
    """Valida una cédula uruguaya (con o sin puntos o guión)."""
    cedula = re.sub(r"\D", "", cedula)
    if len(cedula) < 7 or len(cedula) > 8:
        return False

    cedula = cedula.zfill(8)
    base = [int(x) for x in cedula[:-1]]
    verificador = int(cedula[-1])
    factores = [2, 9, 8, 7, 6, 3, 4]
    total = sum(a * b for a, b in zip(base, factores))
    resto = total % 10
    digito = 0 if resto == 0 else 10 - resto
    return digito == verificador


def validar_email_institucional(email: str, rol: str) -> bool:
    """
    Valida el dominio del correo institucional según el rol:
    - Estudiante: debe terminar en '@correo.ucu.edu.uy'
    - Docente/Admin: debe terminar en '@ucu.edu.uy'
    """
    if rol.lower() == "estudiante":
        return email.endswith("@correo.ucu.edu.uy")
    else:
        return email.endswith("@ucu.edu.uy")

# ==================================================
# NORMALIZACIÓN DE NOMBRES PROPIOS
# ==================================================
def normalizar_nombre(texto):
    if not texto:
        return texto
    
    texto = texto.strip()

    # Permite espacios y apóstrofes manteniendo formato correcto
    partes = texto.split()

    partes_normalizadas = []
    for p in partes:
        if "'" in p:
            # Para casos tipo O'Neill, etc.
            subpartes = p.split("'")
            subpartes = [sp.capitalize() for sp in subpartes]
            p_norm = "'".join(subpartes)
        else:
            p_norm = p.capitalize()

        partes_normalizadas.append(p_norm)

    return " ".join(partes_normalizadas)

# ==================================================
# NORMALIZACIÓN DE NOMBRES DE SALAS
# ==================================================

def normalizar_sala(nombre):
    # Normaliza el nombre: primera letra de cada palabra en mayúscula
    # Respeta apóstrofes para nombres
    palabras = nombre.strip().split()

    normalizadas = []
    for p in palabras:
        if "'" in p:  
            # Casos tipo D'Elía
            partes = p.split("'")
            partes = [parte.capitalize() for parte in partes]
            normalizadas.append("'".join(partes))
        else:
            normalizadas.append(p.capitalize())

    return " ".join(normalizadas)
