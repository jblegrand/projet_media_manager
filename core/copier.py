import hashlib
import shutil
from pathlib import Path
from core.logger import get_logger

logger = get_logger()

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
    Déplace des fichiers de manière hautement sécurisée :
    1. Pre-flight check : Vérification de l'espace disque disponible.
    2. Fichier temporaire (.part) : Évite de laisser un fichier corrompu en cas de coupure de courant.
    3. Copie par blocs et calcul SHA-256 à la volée.
    4. Validation du hash et renommage atomique du fichier.
    """
    total_bytes_global = sum(f["chemin_complet"].stat().st_size for f in fichiers_a_copier)
    bytes_traites_total = 0
    fichiers_crees = []
    
    # --- 1. PRE-FLIGHT CHECK : Vérification de l'espace disque ---
    if fichiers_a_copier:
        premier_dossier_cible = Path(fichiers_a_copier[0]["chemin_cible"]).parent
        premier_dossier_cible.mkdir(parents=True, exist_ok=True)
        _, _, free_space = shutil.disk_usage(premier_dossier_cible)
        
        # Marge de sécurité de 5% pour éviter de saturer le disque à l'octet près
        espace_requis = total_bytes_global * 1.05 
        if free_space < espace_requis:
            msg_err = f"Espace disque insuffisant sur la destination. Requis: {format_size(espace_requis)}, Libre: {format_size(free_space)}."
            logger.error(msg_err)
            raise ValueError(msg_err)

    logger.info(f"--- DÉBUT DE LA COPIE SÉCURISÉE ---")
    logger.info(f"Nombre de fichiers à copier : {len(fichiers_a_copier)} ({format_size(total_bytes_global)})")

    try:
        for f in fichiers_a_copier:
            src = f["chemin_complet"]
            dst = Path(f["chemin_cible"])
            
            # Utilisation d'un fichier temporaire pendant le transfert
            dst_tmp = dst.with_name(dst.name + ".part")
            
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            total_bytes_fichier = src.stat().st_size
            bytes_copiés_fichier = 0
            
            # On trace le fichier temporaire pour le nettoyage en cas d'erreur
            fichiers_crees.append(dst_tmp)
            
            # --- 2. Copie par blocs (RAM safe) vers fichier temporaire ---
            hasher_src = hashlib.sha256()
            with open(src, 'rb') as fsrc, open(dst_tmp, 'wb') as fdst:
                while True:
                    buf = fsrc.read(1024 * 1024 * 10) # 10 Mo
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
            
            # --- 3. Vérification du hash cible sur le fichier temporaire ---
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
            with open(dst_tmp, 'rb') as fdst:
                while True:
                    buf = fdst.read(1024 * 1024 * 10)
                    if not buf:
                        break
                    hasher_dst.update(buf)
            hash_cible = hasher_dst.hexdigest()
            
            # --- 4. Validation et Renommage (Opération Atomique) ---
            if hash_source != hash_cible:
                msg_err = f"Erreur d'intégrité critique pour {src.name}. Corruption pendant le transport."
                logger.error(msg_err)
                raise ValueError(msg_err)
            
            # Le fichier est 100% valide, on le renomme de .part vers .mp4
            # Cette opération est quasi-instantanée (renommage dans l'index du système de fichiers)
            dst_tmp.rename(dst)
            # On remplace la trace pour que le système ne supprime pas le bon fichier si une erreur arrive sur la boucle suivante
            fichiers_crees.remove(dst_tmp) 
            
            logger.info(f"SUCCÈS - Fichier copié : {src.name} -> {dst} (Hash: {hash_cible})")
            
        logger.info(f"--- FIN DE LA COPIE SÉCURISÉE (Toutes les opérations ont réussi) ---")
                
    except BaseException as e:
        # En cas de crash (Arrachage SD, Erreur Streamlit, Bouton Annuler)
        # On supprime les fichiers ".part" incomplets qui traînent
        logger.warning(f"Processus interrompu ou exception levée. Raison : {str(e)}")
        for f_cree in fichiers_crees:
            if f_cree.exists():
                try:
                    f_cree.unlink()
                except Exception:
                    pass
        raise e

def supprimer_fichiers_sources(fichiers: list[dict]):
    """Supprime les fichiers sources originaux après confirmation de l'utilisateur."""
    logger.info(f"--- DÉMARRAGE DE LA SUPPRESSION DE {len(fichiers)} FICHIERS SOURCES ---")
    for f in fichiers:
        src = f["chemin_complet"]
        if src.exists():
            try:
                src.unlink()
                logger.info(f"SUPPRIMÉ - Source : {src}")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression de {src} : {e}")
                print(f"Erreur lors de la suppression de {src} : {e}")
