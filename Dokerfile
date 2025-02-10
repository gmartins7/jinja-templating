# Utilisation de l'image officielle Python (dernière version)
FROM python:3.10-slim

# Définir le répertoire de travail pour le code
WORKDIR /code

# Copier le fichier des dépendances et installer les packages nécessaires
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copier le code de l'application dans /code/app
COPY app/ ./app/

# Exposer le port 4080
EXPOSE 4080

# Définir deux volumes :
# - /data : contiendra les templates de base, intermédiaires et les documents finaux.
# - /code : contiendra le code Python (pour faciliter les mises à jour par bind-mount par exemple).
VOLUME ["/data"]
VOLUME ["/code"]

# Lancer l'API via uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4080"]
