# Usa una imagen base de Python
FROM python:3.10-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia el archivo pyproject.toml al contenedor
COPY pyproject.toml /app/

# Copia la carpeta src al contenedor
COPY src /app/src/

# Instala las dependencias del proyecto en modo editable
RUN pip install --no-cache-dir -e .

# Establece PYTHONPATH para que Python pueda encontrar el paquete src
ENV PYTHONPATH=/app/src

# Expon el puerto (si es necesario, aunque no parece ser necesario en este caso)
EXPOSE 8080

# Por defecto, ejecuta bash para interactuar con el contenedor
CMD ["/bin/bash"]
