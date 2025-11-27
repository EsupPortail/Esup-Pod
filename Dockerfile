# Utilisation de Python 3.12
FROM python:3.12-slim

# Définition du dossier de travail
WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    pkg-config \
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY . .

# On expose toujours le port 8000 en interne (convention Django)
EXPOSE 8000

# On lance Django sur le port 8000 fixe
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]