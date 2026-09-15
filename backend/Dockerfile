FROM python:3.12-slim

# 3.12 a propósito: Pony 0.7.19 sobre 3.13 rompe al iterar los resultados de
# select(). El código usa fetch_all() para no depender de eso, pero la imagen
# se queda en la versión donde el ORM funciona entero.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Solo se usa si el server corriera con SQLite; en prod la base es Neon.
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
