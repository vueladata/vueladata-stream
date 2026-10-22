FROM python:3.12-slim

# Crear usuario no-root 'appuser' para cumplimiento de seguridad (HU-20)
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copiar e instalar dependencias primero (aprovecha la caché de capas de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente y herramientas
COPY . .

# Asignar propiedad de los archivos al usuario sin privilegios
RUN chown -R appuser:appuser /app

# Establecer variables de entorno de ejecución
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src:/app

# Cambiar al usuario sin privilegios
USER appuser

# Ejecutar el simulador productor de eventos OOOI
CMD ["python", "src/producer.py"]
