# Gebruik een officiële Python-runtime als basis
FROM python:3.11-slim

# Stel de werkdirectory in
WORKDIR /app

# Kopieer de requirements.txt naar de container
COPY requirements.txt ./

# Installeer de benodigde Python-pakketten
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de rest van de applicatie naar de container
COPY . .

# Expose de poort waarop de app draait (verander dit indien nodig)
EXPOSE 5000

# Voer de Python-applicatie uit
CMD ["python", "main.py"]
