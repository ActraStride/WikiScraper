FROM python:3.11-slim-buster

WORKDIR /app

COPY pyproject.toml .
COPY src ./src

RUN pip install .

CMD ["wiki", "--help"]

#  NO DEFINIMOS UN CMD AQUÍ PARA LA CLI.
#  DEJAREMOS QUE EL COMANDO SEA ESPECIFICADO AL EJECUTAR CON docker-compose run