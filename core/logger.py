import logging
import os
from pathlib import Path

# Création du dossier logs à la racine du projet
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "media_manager.log"

# Configuration du logger principal
logger = logging.getLogger("MediaManager")
logger.setLevel(logging.INFO)

# Évite d'ajouter plusieurs fois le même handler si le module est rechargé par Streamlit
if not logger.handlers:
    # Handler pour écrire dans le fichier
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Format des messages de log : [Date Heure] - NIVEAU - Message
    formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)

def get_logger():
    return logger
