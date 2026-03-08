FROM python:3.12-slim

WORKDIR /app

# Dipendenze di sistema per chromadb (build tools per compilare C extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*

# Installare dipendenze Python (layer cacheable)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiare il codice
COPY . .

# Directory dati (il volume persistente viene montato qui)
RUN mkdir -p data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
