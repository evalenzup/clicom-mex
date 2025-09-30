# Usa una imagen base oficial de Python.
FROM python:3.11-slim

# Crea un usuario no-root
RUN adduser --system --group appuser

# Establece el directorio de trabajo en /code
WORKDIR /code

# Copia el archivo de requisitos primero para aprovechar el cache de Docker
COPY backend/requirements.txt requirements.txt

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la aplicación
COPY backend/app /code/app

# Copia el frontend compilado para ser servido por FastAPI
COPY frontend/dist /code/app/static

# Cambia el propietario del directorio /code al usuario appuser
RUN chown -R appuser:appuser /code

# Cambia al usuario no-root
USER appuser

# Expone el puerto en el que corre la aplicación
EXPOSE 8000

# Comando para correr la aplicación usando uvicorn
# El host 0.0.0.0 hace que sea accesible desde fuera del contenedor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
