import os
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
try:
    from hachoir.parser import createParser
    from hachoir.metadata import extractMetadata
    HACHOIR_DISPONIBLE = True
except ImportError:
    HACHOIR_DISPONIBLE = False

# ==========================================
# CONFIGURATION
# ==========================================
DOSSIER_UTILISATEUR = Path(r"C:\Users\jb_le")

# Liste corrigée (sans espace)
SOUS_DOSSIERS_CIBLES = [
    "Bureau",
    "Images",
    "Téléchargements",
    "Vidéos",
    "Appels enregistrés",
    "Contacts",
    "Documents",
    "Favorites",
    "Liens",
    "Musique",
    "Objets 3D",
    "Parties enregistrées",
    "Recherches"
]

DOSSIER_DESTINATION = Path(r"D:\Vidéos")
EXTENSIONS_VIDEO = {".mp4", ".mov", ".MP4", ".MOV"}

# MODE SIMULATION (True = affiche sans modifier | False = exécute la copie)
MODE_SIMULATION = True 

def calculer_sha256(chemin_fichier):
    """Calcule l'empreinte SHA-256 d'un fichier pour vérifier l'intégrité après copie."""
    hasher = hashlib.sha256()
    with open(chemin_fichier, "rb") as f:
        while True:
            bloc = f.read(65536)
            if not bloc:
                break
            hasher.update(bloc)
    return hasher.hexdigest()

def obtenir_date_prise_de_vue(chemin_fichier):
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

def executer_tri_dji():
    DOSSIER_DESTINATION.mkdir(parents=True, exist_ok=True)
    
    print(f"{'=== MODE SIMULATION (Dry Run) ===' if MODE_SIMULATION else '=== MODE EXECUTION REEL ==='}\n")
    
    total_traite = 0
    total_succes = 0

    for nom_dossier in SOUS_DOSSIERS_CIBLES:
        chemin_dossier = DOSSIER_UTILISATEUR / nom_dossier
        if not chemin_dossier.exists():
            continue
            
        print(f"Analyse du dossier : {chemin_dossier}")
        
        for chemin_fichier in chemin_dossier.rglob("*"):
            if chemin_fichier.is_file() and chemin_fichier.suffix in EXTENSIONS_VIDEO:
                nom_fichier = chemin_fichier.name
                
                if nom_fichier.lower().startswith("dji"):
                    total_traite += 1
                    
                    dt = obtenir_date_prise_de_vue(chemin_fichier)
                    date_str = dt.strftime("%Y%m%d_%H%M")
                    
                    nouveau_nom = f"DJI_{date_str}{chemin_fichier.suffix}"
                    chemin_cible = DOSSIER_DESTINATION / nouveau_nom

                    compteur_doublon = 1
                    while chemin_cible.exists():
                        nouveau_nom = f"DJI_{date_str}_{compteur_doublon}{chemin_fichier.suffix}"
                        chemin_cible = DOSSIER_DESTINATION / nouveau_nom
                        compteur_doublon += 1

                    print(f"  [TROUVÉ] {chemin_fichier.name} -> {nouveau_nom}")

                    if not MODE_SIMULATION:
                        try:
                            shutil.copy2(chemin_fichier, chemin_cible)
                            
                            hash_source = calculer_sha256(chemin_fichier)
                            hash_cible = calculer_sha256(chemin_cible)
                            
                            if hash_source == hash_cible:
                                chemin_fichier.unlink()
                                print(f"    [SUCCES] Copie vérifiée et source supprimée.")
                                total_succes += 1
                            else:
                                print(f"    [ERREUR] Incohérence de hachage. Fichier conservé.")
                                if chemin_cible.exists():
                                    chemin_cible.unlink()
                        except Exception as e:
                            print(f"    [ERREUR] {e}")

    print(f"\nBilan : {total_traite} fichiers DJI identifiés.")
    if MODE_SIMULATION:
        print("💡 Mode Simulation actif : aucun fichier n'a été modifié.")

if __name__ == "__main__":
    executer_tri_dji()