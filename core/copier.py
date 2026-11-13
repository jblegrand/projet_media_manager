import hashlib
from pathlib import Path

def format_size(bytes_size):
    """Formate une taille en octets vers une unité lisible (Ko, Mo, Go)."""
    if bytes_size < 1024**2:
        return f"{bytes_size / 1024:.2f} Ko"
    elif bytes_size < 1024**3:
        return f"{bytes_size / (1024**2):.2f} Mo"
    else:
        return f"{bytes_size / (1024**3):.2f} Go"

def deplacer_fichiers_securise(fichiers_a_copier: list[dict], update_callback=None):
    """
    Déplace des fichiers de manière sécurisée en 3 étapes :
    1. Copie du fichier par blocs (avec calcul de l'empreinte SHA-256 à la volée).
    2. Vérification de l'empreinte SHA-256 du fichier cible.
    3. Si les empreintes correspondent, suppression du fichier source d'origine.
    
    Cette méthode évite le chargement en RAM et permet d'annuler/suivre la progression.
    """
    total_bytes_global = sum(f["chemin_complet"].stat().st_size for f in fichiers_a_copier)
    bytes_traites_total = 0
    fichiers_crees = []
    
    try:
        for f in fichiers_a_copier:
            src = f["chemin_complet"]
            dst = Path(f["chemin_cible"])
            
            # Création du dossier parent de la destination si nécessaire
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            total_bytes_fichier = src.stat().st_size
            bytes_copiés_fichier = 0
            
            # On mémorise le fichier cible pour pouvoir le nettoyer si l'utilisateur annule
            fichiers_crees.append(dst)
            
            # 1. Copie par blocs avec calcul du hash source à la volée
            hasher_src = hashlib.sha256()
            with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
                while True:
                    buf = fsrc.read(1024 * 1024 * 10) # Traitement par blocs de 10 Mo
                    if not buf:
                        break
                    
                    hasher_src.update(buf)
                    fdst.write(buf)
                    
                    bytes_copiés_fichier += len(buf)
                    bytes_traites_total += len(buf)
                    
                    if update_callback:
                        update_callback(
                            src.name,
                            "Copie en cours...",
                            bytes_copiés_fichier,
                            total_bytes_fichier,
                            bytes_traites_total,
                            total_bytes_global
                        )
            
            hash_source = hasher_src.hexdigest()
            
            # 2. Vérification du hash cible en relisant le fichier de destination
            if update_callback:
                update_callback(
                    src.name, 
                    "Vérification de l'intégrité (hachage)...", 
                    total_bytes_fichier, 
                    total_bytes_fichier, 
                    bytes_traites_total, 
                    total_bytes_global
                )
                
            hasher_dst = hashlib.sha256()
            with open(dst, 'rb') as fdst:
                while True:
                    buf = fdst.read(1024 * 1024 * 10)
                    if not buf:
                        break
                    hasher_dst.update(buf)
            hash_cible = hasher_dst.hexdigest()
            
            # 3. Validation
            if hash_source != hash_cible:
                raise ValueError(f"Erreur d'intégrité critique pour {src.name}. Annulation du processus.")
                
    except BaseException as e:
        # Streamlit lève une exception lorsqu'on clique sur "Annuler" (pour forcer le rechargement).
        # On l'intercepte ici (ainsi que toute autre erreur) pour nettoyer les fichiers à moitié copiés.
        for f_cree in fichiers_crees:
            if f_cree.exists():
                try:
                    f_cree.unlink()
                except Exception:
                    pass
        raise e

def supprimer_fichiers_sources(fichiers: list[dict]):
    """Supprime les fichiers sources originaux après confirmation de l'utilisateur."""
    for f in fichiers:
        src = f["chemin_complet"]
        if src.exists():
            try:
                src.unlink()
            except Exception as e:
                print(f"Erreur lors de la suppression de {src} : {e}")
