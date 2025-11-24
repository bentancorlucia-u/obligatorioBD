FROM python:3.11-slim

# Carpeta de trabajo
WORKDIR /app

# Dependencias necesarias para mysql-connector
RUN apt-get update && apt-get install -y default-libmysqlclient-dev gcc && apt-get clean

# Copiar requirements desde backend
COPY backend/requirements.txt /app/requirements.txt

# Instalar Python requirements
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar backend + frontend completos
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Exponer Flask
EXPOSE 5000

# Comando principal
CMD ["python", "backend/app.py"]
