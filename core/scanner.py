import os
from pathlib import Path
from datetime import datetime
from core.logger import get_logger

logger = get_logger()

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

def fichiers_identiques(chemin_src: Path, chemin_dst: Path) -> bool:
    """
    Vérifie si deux fichiers sont identiques.
    Pour l'instant, on se base uniquement sur la taille exacte en octets pour des raisons de performance
    sur de gros fichiers vidéo. Si les tailles sont identiques à l'octet près, on considère que c'est un doublon.
    """
    if not chemin_dst.exists():
        return False
    return chemin_src.stat().st_size == chemin_dst.stat().st_size

def calculer_chemin_cible_avec_doublons(dossier_destination: Path, fichier_source: Path, date_prise: datetime) -> tuple[str, Path, bool]:
    """
    Calcule le nouveau nom, le chemin cible, et indique si le fichier est un doublon exact déjà présent.
    Si le nom est pris mais le fichier est différent, incrémente le compteur (_1, _2).
    """
    suffixe = fichier_source.suffix
    date_str = date_prise.strftime("%Y%m%d_%H%M")
    nouveau_nom = f"DJI_{date_str}{suffixe}"
    chemin_cible = dossier_destination / nouveau_nom

    compteur_doublon = 1
    est_doublon = False

    while chemin_cible.exists():
        # Si le fichier existe, on vérifie si c'est strictement le même (taille identique)
        if fichiers_identiques(fichier_source, chemin_cible):
            est_doublon = True
            logger.info(f"Doublon exact détecté : {fichier_source.name} (Taille: {fichier_source.stat().st_size} octets)")
            break
            
        # Si c'est un fichier différent (même minute de vol mais vidéo différente), on cherche un nouveau nom
        nouveau_nom = f"DJI_{date_str}_{compteur_doublon}{suffixe}"
        chemin_cible = dossier_destination / nouveau_nom
        compteur_doublon += 1
        
    return nouveau_nom, chemin_cible, est_doublon

def trouver_fichiers_dji(dossiers_sources: list[str], dossier_destination: str) -> list[dict]:
    """
    Parcourt une liste de dossiers sources pour trouver les fichiers vidéo DJI.
    Retourne une liste de dictionnaires contenant les informations des fichiers trouvés et leur cible.
    """
    fichiers_trouves = []
    chemin_dest = Path(dossier_destination)
    
    logger.info(f"--- DÉMARRAGE D'UN NOUVEAU SCAN ---")
    logger.info(f"Dossiers sources : {dossiers_sources}")
    logger.info(f"Dossier destination : {dossier_destination}")
    
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
                    nouveau_nom, chemin_cible, est_doublon = calculer_chemin_cible_avec_doublons(chemin_dest, chemin_fichier, date_prise)
                    
                    fichiers_trouves.append({
                        "selectionne": not est_doublon,  # Décoché par défaut si c'est un doublon
                        "est_doublon": est_doublon,
                        "chemin_complet": chemin_fichier,
                        "nom_original": nom_fichier,
                        "dossier_source": str(chemin_dossier),
                        "date_prise_vue": date_prise,
                        "nouveau_nom": nouveau_nom,
                        "chemin_cible": str(chemin_cible),
                        "taille_go": chemin_fichier.stat().st_size / (1024 ** 3)  # On garde la précision totale dans le dictionnaire
                    })
                    
    logger.info(f"Fin du scan : {len(fichiers_trouves)} fichiers DJI identifiés.")
    return fichiers_trouves
