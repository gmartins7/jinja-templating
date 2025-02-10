"""
API pour générer des documents à partir de templates.
Utilise FastAPI et Jinja2 pour générer :
- Un template intermédiaire à partir d’un template de base.
- Un document final à partir d’un template intermédiaire.
- La génération de documents pour tous les mois d’une année donnée.
- La liste des templates de base et intermédiaires.
- La récupération d’information sur un document généré.
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import os
import calendar
import datetime
from jinja2 import Template

# Initialisation de l'application FastAPI avec la doc Swagger intégrée
app = FastAPI(
    title="Template Document Generator API",
    description="API pour générer des templates intermédiaires et des documents finaux à partir de templates de base avec FastAPI et Jinja2.",
    version="1.0.0"
)

# Définition des répertoires utilisés
BASE_TEMPLATE_DIR = "/data/base"
INTERMEDIATE_TEMPLATE_DIR = "/data/intermediate"
FINAL_DOCUMENT_DIR = "/data/final"

# Création des dossiers si nécessaire
for directory in [BASE_TEMPLATE_DIR, INTERMEDIATE_TEMPLATE_DIR, FINAL_DOCUMENT_DIR]:
    os.makedirs(directory, exist_ok=True)

# -------------
# Modèles de données (Pydantic)
# -------------

class IntermediateTemplateRequest(BaseModel):
    base_template_name: str = Field(..., description="Nom du template de base situé dans /data/base")
    tenant_info: List[str] = Field(..., min_items=3, max_items=3, description="Liste de 3 lignes d'informations locataire")
    tenant_number: str = Field(..., description="Numéro de locataire au format MM/YYYY")
    address: List[str] = Field(..., min_items=4, max_items=4, description="Liste de 4 lignes correspondant à l'adresse")
    amount: float = Field(..., description="Montant (nombre réel)")
    intermediate_template_name: str = Field(..., description="Nom du template intermédiaire généré")

    @validator('tenant_number')
    def validate_tenant_number(cls, v):
        # Vérification du format MM/YYYY
        if len(v) != 7 or v[2] != '/':
            raise ValueError("Le numéro de locataire doit être au format MM/YYYY")
        month = v[:2]
        year = v[3:]
        if not (month.isdigit() and year.isdigit()):
            raise ValueError("Le numéro de locataire doit contenir uniquement des chiffres")
        if not (1 <= int(month) <= 12):
            raise ValueError("Le mois doit être compris entre 01 et 12")
        return v

class DocumentRequest(BaseModel):
    intermediate_template_name: str = Field(..., description="Nom du template intermédiaire situé dans /data/intermediate")
    year: Optional[int] = Field(None, description="Année pour la génération du document (valeur par défaut : année courante)")
    month: Optional[int] = Field(None, ge=1, le=12, description="Mois (1-12) pour la génération du document (valeur par défaut : mois courant)")

class AllDocumentsRequest(BaseModel):
    intermediate_template_name: str = Field(..., description="Nom du template intermédiaire")
    year: Optional[int] = Field(None, description="Année pour générer l'ensemble des documents (valeur par défaut : année courante)")

# -------------
# Fonctions utilitaires
# -------------

def get_first_last_day(year: int, month: int):
    """
    Calcule le premier et le dernier jour du mois au format DD/MM/YYYY.
    """
    first_day = datetime.date(year, month, 1).strftime("%d/%m/%Y")
    last_day_num = calendar.monthrange(year, month)[1]
    last_day = datetime.date(year, month, last_day_num).strftime("%d/%m/%Y")
    return first_day, last_day

def render_template(template_str: str, context: dict) -> str:
    """
    Rend le template avec Jinja2 en utilisant le contexte fourni.
    """
    template = Template(template_str)
    return template.render(**context)

# -------------
# Endpoints de l'API
# -------------

@app.post("/generate-intermediate-template", summary="Générer un template intermédiaire à partir d'un template de base")
def generate_intermediate_template(request: IntermediateTemplateRequest):
    """
    Génère un template intermédiaire en utilisant un template de base et les informations fournies (informations locataire, numéro, adresse et montant).
    
    Le template de base est lu dans /data/base et le template intermédiaire généré est enregistré dans /data/intermediate.
    """
    base_template_path = os.path.join(BASE_TEMPLATE_DIR, request.base_template_name)
    if not os.path.isfile(base_template_path):
        raise HTTPException(status_code=404, detail="Template de base non trouvé")
    
    try:
        with open(base_template_path, "r", encoding="utf-8") as f:
            base_template_content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la lecture du template de base : {e}")

    # Contexte pour le rendu avec Jinja2
    context = {
        "tenant_info": request.tenant_info,
        "tenant_number": request.tenant_number,
        "address": request.address,
        "amount": request.amount
    }

    try:
        rendered_content = render_template(base_template_content, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du rendu du template intermédiaire : {e}")

    # Enregistrement du template intermédiaire dans /data/intermediate
    intermediate_template_path = os.path.join(INTERMEDIATE_TEMPLATE_DIR, request.intermediate_template_name)
    try:
        with open(intermediate_template_path, "w", encoding="utf-8") as f:
            f.write(rendered_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'écriture du template intermédiaire : {e}")

    return {"message": "Template intermédiaire généré avec succès", "file": request.intermediate_template_name}

@app.post("/generate-document", summary="Générer un document final à partir d'un template intermédiaire")
def generate_document(request: DocumentRequest):
    """
    Génère un document final à partir d'un template intermédiaire.
    
    Si l'année ou le mois ne sont pas renseignés, la date courante est utilisée.
    Le document final est enregistré dans /data/final/<template_intermédiaire>/<année> avec un nom reprenant le template, le mois et l'année.
    """
    now = datetime.datetime.now()
    year = request.year if request.year is not None else now.year
    month = request.month if request.month is not None else now.month

    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Le mois doit être compris entre 1 et 12")
    
    # Calcul du premier et du dernier jour du mois
    first_day, last_day = get_first_last_day(year, month)

    intermediate_template_path = os.path.join(INTERMEDIATE_TEMPLATE_DIR, request.intermediate_template_name)
    if not os.path.isfile(intermediate_template_path):
        raise HTTPException(status_code=404, detail="Template intermédiaire non trouvé")
    
    try:
        with open(intermediate_template_path, "r", encoding="utf-8") as f:
            intermediate_template_content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la lecture du template intermédiaire : {e}")
    
    # Contexte pour le rendu du document final
    context = {
        "first_day": first_day,
        "last_day": last_day,
        "year": year,
        "month": f"{month:02d}"
    }

    try:
        final_document_content = render_template(intermediate_template_content, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du rendu du document final : {e}")
    
    # Création du dossier pour le document final : /data/final/<template_intermédiaire>/<année>
    final_dir = os.path.join(FINAL_DOCUMENT_DIR, request.intermediate_template_name, str(year))
    os.makedirs(final_dir, exist_ok=True)
    final_filename = f"{request.intermediate_template_name}_{month:02d}_{year}.html"
    final_document_path = os.path.join(final_dir, final_filename)

    try:
        with open(final_document_path, "w", encoding="utf-8") as f:
            f.write(final_document_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'écriture du document final : {e}")
    
    return {"message": "Document final généré avec succès", "file": final_filename, "path": final_document_path}

@app.post("/generate-all-documents", summary="Générer tous les documents d'un template intermédiaire pour une année donnée")
def generate_all_documents(request: AllDocumentsRequest):
    """
    Génère un document final pour chaque mois (de janvier à décembre) pour le template intermédiaire spécifié.
    
    Si l'année n'est pas fournie, l'année courante est utilisée.
    """
    now = datetime.datetime.now()
    year = request.year if request.year is not None else now.year
    generated_files = []

    for month in range(1, 13):
        # Création d'une requête pour chaque mois
        doc_request = DocumentRequest(intermediate_template_name=request.intermediate_template_name, year=year, month=month)
        result = generate_document(doc_request)
        generated_files.append(result["file"])
    
    return {"message": "Documents générés pour tous les mois", "files": generated_files}

@app.get("/list-base-templates", summary="Lister les templates de base")
def list_base_templates():
    """
    Liste les fichiers de template de base présents dans le répertoire /data/base.
    """
    try:
        files = os.listdir(BASE_TEMPLATE_DIR)
        base_templates = [f for f in files if os.path.isfile(os.path.join(BASE_TEMPLATE_DIR, f))]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du listing des templates de base : {e}")
    return {"base_templates": base_templates}

@app.get("/list-intermediate-templates", summary="Lister les templates intermédiaires")
def list_intermediate_templates():
    """
    Liste les fichiers de template intermédiaire présents dans le répertoire /data/intermediate.
    """
    try:
        files = os.listdir(INTERMEDIATE_TEMPLATE_DIR)
        intermediate_templates = [f for f in files if os.path.isfile(os.path.join(INTERMEDIATE_TEMPLATE_DIR, f))]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du listing des templates intermédiaires : {e}")
    return {"intermediate_templates": intermediate_templates}

@app.get("/document-info", summary="Récupérer le nom d'un document généré")
def get_document_info(
    intermediate_template_name: str = Query(..., description="Nom du template intermédiaire"),
    year: int = Query(..., description="Année du document"),
    month: int = Query(..., ge=1, le=12, description="Mois (1-12) du document")
):
    """
    Retourne le nom et le chemin du document final généré pour le template intermédiaire, l'année et le mois spécifiés.
    
    Si le document n'existe pas, renvoie une erreur 404.
    """
    final_dir = os.path.join(FINAL_DOCUMENT_DIR, intermediate_template_name, str(year))
    final_filename = f"{intermediate_template_name}_{month:02d}_{year}.html"
    final_document_path = os.path.join(final_dir, final_filename)
    if not os.path.isfile(final_document_path):
        raise HTTPException(status_code=404, detail="Document non généré")
    return {"document": final_filename, "path": final_document_path}
