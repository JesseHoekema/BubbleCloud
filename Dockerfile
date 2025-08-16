FROM python:3.11-slim-bullseye

WORKDIR /app

RUN apt-get update && apt-get upgrade -y && apt-get clean

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt gunicorn

COPY . .

CMD ["gunicorn", "-b", "0.0.0.0:5923", "main:app"]
