# jinja-templating : Template Document Generator API
Génération de templates intermédiaires et de documents via api

Ce projet met en place une API utilisant **FastAPI** et **Jinja2** afin de générer des documents à partir de templates.
L’API permet de :
- Générer un **template intermédiaire** à partir d’un template de base.
- Générer un **document final** à partir d’un template intermédiaire, en calculant le premier et le dernier jour du mois.
- Générer les documents pour **tous les mois** d’une année donnée.
- Lister les templates de base et intermédiaires.
- Récupérer le nom d’un document généré.

## Structure du projet

- **Dockerfile**  
  Construit l’image Docker basée sur la dernière version de Python, installe les dépendances depuis `requirements.txt` et définit deux volumes :
  - `/data` : contiendra les templates de base, intermédiaires et les documents finaux.
  - `/code` : contiendra le code Python de l’API.

- **docker-compose.yml**  
  Fichier de configuration Docker Compose qui effectue le build de l’image et mappe les volumes et le port 4080.

- **requirements.txt**  
  Liste des packages Python requis :
  - fastapi
  - uvicorn[standard]
  - jinja2

- **app/main.py**  
  Code de l’API contenant :
  - Un endpoint pour générer un template intermédiaire.
  - Un endpoint pour générer un document final.
  - Un endpoint pour générer tous les documents d’un template intermédiaire pour une année donnée.
  - Des endpoints pour lister les templates et obtenir les informations d’un document.

- **README.md**  
  Ce fichier décrivant le projet et expliquant la démarche.

## Endpoints disponibles

1. **Générer un template intermédiaire**
   - **URL**: `/generate-intermediate-template`
   - **Méthode**: POST
   - **Description**: Génère un template intermédiaire à partir d’un template de base en utilisant les informations locataire, l’adresse et le montant.
   - **Corps de la requête** (JSON):
     - `base_template_name` : Nom du template de base (dans `/data/base`)
     - `tenant_info` : Liste de 3 chaînes de caractères (informations locataire)
     - `tenant_number` : Numéro de locataire au format `MM/YYYY`
     - `address` : Liste de 4 chaînes (adresse)
     - `amount` : Nombre réel
     - `intermediate_template_name` : Nom pour le template intermédiaire généré

2. **Générer un document final**
   - **URL**: `/generate-document`
   - **Méthode**: POST
   - **Description**: Génère un document final à partir d’un template intermédiaire. Si l’année ou le mois ne sont pas fournis, la date courante est utilisée.
   - **Corps de la requête** (JSON):
     - `intermediate_template_name` : Nom du template intermédiaire (dans `/data/intermediate`)
     - `year` (optionnel) : Année
     - `month` (optionnel) : Mois (entre 1 et 12)

3. **Générer tous les documents d'une année**
   - **URL**: `/generate-all-documents`
   - **Méthode**: POST
   - **Description**: Génère les documents pour tous les mois (de janvier à décembre) pour un template intermédiaire donné. L’année par défaut est l’année courante.
   - **Corps de la requête** (JSON):
     - `intermediate_template_name` : Nom du template intermédiaire
     - `year` (optionnel) : Année

4. **Lister les templates de base**
   - **URL**: `/list-base-templates`
   - **Méthode**: GET
   - **Description**: Retourne la liste des templates de base présents dans `/data/base`.

5. **Lister les templates intermédiaires**
   - **URL**: `/list-intermediate-templates`
   - **Méthode**: GET
   - **Description**: Retourne la liste des templates intermédiaires présents dans `/data/intermediate`.

6. **Obtenir les informations d'un document généré**
   - **URL**: `/document-info`
   - **Méthode**: GET
   - **Description**: Renvoie le nom et le chemin du document généré pour un template intermédiaire, une année et un mois donnés. Renvoie une erreur 404 si le document n’existe pas.
   - **Paramètres de requête**:
     - `intermediate_template_name` : Nom du template intermédiaire
     - `year` : Année du document
     - `month` : Mois du document (entre 1 et 12)

## Lancement de l'application

### Prérequis
- Docker
- Docker Compose

### Étapes

1. **Cloner le dépôt**
   ```bash
   git clone <url_du_dépôt>
   cd <nom_du_dépôt>

