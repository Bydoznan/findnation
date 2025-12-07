# FROM python:3.11-slim

# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# EXPOSE 8000
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# # -----------------------------------------
# # Dockerfile dla Central Lost & Found API
# # -----------------------------------------

FROM python:3.11-slim

# Ustawienie workdir
WORKDIR /app

# Instalacja zależności systemowych
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Kopiowanie requirements.txt
COPY requirements.txt .

# Instalacja zależności Pythona
RUN pip install --no-cache-dir -r requirements.txt

# Kopiowanie całego backendu
COPY . .

# Uruchomienie serwera FastAPI (Uvicorn)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
