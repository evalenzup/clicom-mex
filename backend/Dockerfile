# Usa una imagen base oficial de Python.
FROM python:3.11-slim

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo de requisitos primero para aprovechar el cache de Docker
COPY requirements.txt requirements.txt

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la aplicación
COPY ./app /app/app

# Expone el puerto en el que corre la aplicación
EXPOSE 8000

# Comando para correr la aplicación usando uvicorn
# El host 0.0.0.0 hace que sea accesible desde fuera del contenedor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
