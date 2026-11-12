import os
from pathlib import Path
from datetime import datetime

try:
    from hachoir.parser import createParser
    from hachoir.metadata import extractMetadata
    HACHOIR_DISPONIBLE = True
except ImportError:
    HACHOIR_DISPONIBLE = False

EXTENSIONS_VIDEO = {".mp4", ".mov", ".MP4", ".MOV"}

def obtenir_date_prise_de_vue(chemin_fichier: Path) -> datetime:
    """Extrait la date de prise de vue des métadonnées de la vidéo (ou fallback sur la date de modif)."""
    if HACHOIR_DISPONIBLE:
        try:
            parser = createParser(str(chemin_fichier))
            if parser:
                metadata = extractMetadata(parser)
                if metadata:
                    date_creation = metadata.get('creation_date')
                    if date_creation:
                        return date_creation
        except Exception:
            pass
    
    try:
        timestamp = chemin_fichier.stat().st_mtime
        return datetime.fromtimestamp(timestamp)
    except Exception:
        return datetime.now()

def calculer_chemin_cible(dossier_destination: Path, date_prise: datetime, suffixe: str) -> tuple[str, Path]:
    """
    Calcule le nouveau nom du fichier et son chemin cible dans le dossier de destination,
    en gérant les conflits de noms (doublons).
    """
    date_str = date_prise.strftime("%Y%m%d_%H%M")
    nouveau_nom = f"DJI_{date_str}{suffixe}"
    chemin_cible = dossier_destination / nouveau_nom

    compteur_doublon = 1
    while chemin_cible.exists():
        nouveau_nom = f"DJI_{date_str}_{compteur_doublon}{suffixe}"
        chemin_cible = dossier_destination / nouveau_nom
        compteur_doublon += 1
        
    return nouveau_nom, chemin_cible

def trouver_fichiers_dji(dossiers_sources: list[str], dossier_destination: str) -> list[dict]:
    """
    Parcourt une liste de dossiers sources pour trouver les fichiers vidéo DJI.
    Retourne une liste de dictionnaires contenant les informations des fichiers trouvés et leur cible.
    """
    fichiers_trouves = []
    chemin_dest = Path(dossier_destination)
    
    for dossier_source in dossiers_sources:
        chemin_dossier = Path(dossier_source)
        if not chemin_dossier.exists() or not chemin_dossier.is_dir():
            continue
            
        for chemin_fichier in chemin_dossier.rglob("*"):
            if chemin_fichier.is_file() and chemin_fichier.suffix in EXTENSIONS_VIDEO:
                nom_fichier = chemin_fichier.name
                
                # On identifie les fichiers DJI par leur nom (peut être étendu)
                if nom_fichier.lower().startswith("dji"):
                    date_prise = obtenir_date_prise_de_vue(chemin_fichier)
                    nouveau_nom, chemin_cible = calculer_chemin_cible(chemin_dest, date_prise, chemin_fichier.suffix)
                    
                    fichiers_trouves.append({
                        "chemin_complet": chemin_fichier,
                        "nom_original": nom_fichier,
                        "dossier_source": str(chemin_dossier),
                        "date_prise_vue": date_prise,
                        "nouveau_nom": nouveau_nom,
                        "chemin_cible": str(chemin_cible)
                    })
                    
    return fichiers_trouves
