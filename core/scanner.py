import re
from pathlib import Path
from datetime import datetime
from core.logger import get_logger

logger = get_logger()

try:
    from hachoir.parser import createParser
    from hachoir.metadata import extractMetadata
    HACHOIR_DISPONIBLE = True
    # Force Hachoir à être silencieux pour éviter de polluer la console avec des erreurs EXIF mineures
    import hachoir.core.config
    hachoir.core.config.quiet = True
except ImportError:
    HACHOIR_DISPONIBLE = False
        
try:
    import exifread
    EXIFREAD_DISPONIBLE = True
except ImportError:
    EXIFREAD_DISPONIBLE = False

EXTENSIONS_VIDEO = {
    ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v",
    ".mpg", ".mpeg", ".3gp", ".mts", ".m2ts"
}

EXTENSIONS_PHOTO = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp",
    ".raw", ".cr2", ".cr3", ".nef", ".arw", ".dng", ".orf", ".rw2"
}

def obtenir_date_prise_de_vue(chemin_fichier: Path) -> datetime:
    """Extrait la date de prise de vue des métadonnées de la vidéo ou photo (ou fallback sur la date de modif)."""
    if HACHOIR_DISPONIBLE:
        # On capture les logs d'erreurs de hachoir pour éviter de polluer la console Streamlit
        import hachoir.core.config
        hachoir.core.config.quiet = True
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

def obtenir_marque_appareil(chemin_fichier: Path) -> str:
    """Tente d'extraire la marque de l'appareil (ex: Canon, Nikon) depuis les métadonnées EXIF d'une photo."""
    if EXIFREAD_DISPONIBLE and chemin_fichier.suffix.lower() in EXTENSIONS_PHOTO:
        try:
            with open(chemin_fichier, 'rb') as f:
                # 'details=False' pour aller plus vite (on ne veut que les tags principaux)
                tags = exifread.process_file(f, details=False)
                if "Image Make" in tags:
                    marque = str(tags["Image Make"]).strip()
                    # On nettoie un peu la marque (enlever les espaces, caractères bizarres, et majuscules)
                    marque = marque.split('\x00')[0] # Retire les potentiels null-bytes
                    marque = marque.split(' ')[0] # Prend juste le premier mot (ex: "Canon" au lieu de "Canon Corporation")
                    marque = "".join(c for c in marque if c.isalnum()) # Garde que l'alphanumérique
                    if marque:
                        return marque.upper()
        except Exception:
            pass
    return "CAMERA"

def identifier_categorie_media(nom_fichier: str, est_video: bool, est_raw: bool, fichier_source: Path = None) -> dict:
    """
    Analyse le nom du fichier pour déterminer sa catégorie, son dossier de destination
    et s'il doit être renommé avec la date.
    Différencie le traitement s'il s'agit d'une vidéo ou d'une photo.
    """
    nom_min = nom_fichier.lower()

    # 1. Traitement des VIDÉOS
    if est_video:
        if nom_min.startswith("dji"):
            return {"dossier_base": "Vidéos/Drone", "prefixe": "DJI", "renommer": True, "classer_par_date": False}
        elif nom_min.startswith(("gopr", "gh", "gx")):
            return {"dossier_base": "Vidéos/ActionCam", "prefixe": "GOPRO", "renommer": True, "classer_par_date": False}
        elif nom_min.startswith("mvi_"):
            return {"dossier_base": "Vidéos/Appareil Photo", "prefixe": "CAMERA", "renommer": True, "classer_par_date": False}
        elif nom_min.startswith("p") and len(fichier_source.stem) >= 4 and fichier_source.stem[1:4].isdigit():
            # Ex: P1060236.MOV (Panasonic Lumix)
            return {"dossier_base": "Vidéos/Appareil Photo", "prefixe": "PANASONIC", "renommer": True, "classer_par_date": False}
        elif nom_min.startswith("dscf"):
            return {"dossier_base": "Vidéos/Camera Chasse", "prefixe": "CHASSE", "renommer": True, "classer_par_date": False}
        elif nom_min.startswith(("vid_", "pxl_", "img_")):
            return {"dossier_base": "Vidéos/Téléphone", "prefixe": "PHONE", "renommer": True, "classer_par_date": False}

        # Fallback : Vidéo non reconnue par ses préfixes
            return {"dossier_base": "Vidéos/Montage", "prefixe": "", "renommer": False, "classer_par_date": False}

    # 2. Traitement des PHOTOS (JPG, PNG, etc. et RAW)
    else:
        dossier_racine = "Images/RAW" if est_raw else "Images/JPG"

        if nom_min.startswith("dji"):
            return {"dossier_base": dossier_racine, "prefixe": "DJI", "renommer": True, "classer_par_date": True}
        elif nom_min.startswith(("gopr", "gh", "gx")):
            return {"dossier_base": dossier_racine, "prefixe": "GOPRO", "renommer": True, "classer_par_date": True}
        elif nom_min.startswith("mvi_") or nom_min.startswith("img_") or nom_min.startswith("dsc") and not nom_min.startswith("dscf"):
            prefixe_marque = obtenir_marque_appareil(fichier_source) if fichier_source else "CAMERA"
            return {"dossier_base": dossier_racine, "prefixe": prefixe_marque, "renommer": True, "classer_par_date": True}
        elif nom_min.startswith("p") and len(fichier_source.stem) >= 4 and fichier_source.stem[1:4].isdigit():
            # Ex: P1060255.JPG (Panasonic Lumix). Force la marque car l'EXIF est souvent capricieux.
            return {"dossier_base": dossier_racine, "prefixe": "PANASONIC", "renommer": True, "classer_par_date": True}
        elif nom_min.startswith("dscf"):
            return {"dossier_base": dossier_racine, "prefixe": "CHASSE", "renommer": True, "classer_par_date": True}
        elif nom_min.startswith("pxl_") or (nom_min.startswith("img_") and "vid" not in nom_min):
            return {"dossier_base": dossier_racine, "prefixe": "PHONE", "renommer": True, "classer_par_date": True}
        elif len(fichier_source.stem) == 8 and fichier_source.stem.isdigit():
            # Ex: 92740003.JPG (8 chiffres) issus de numérisation de pellicule 35mm
            return {"dossier_base": dossier_racine, "prefixe": "ANALOGIQUE", "renommer": True, "classer_par_date": True}
        else:
            # Fallback (photo d'origine inconnue, on essaie quand même d'extraire la marque au cas où)
            prefixe_marque = obtenir_marque_appareil(fichier_source) if fichier_source else "PHOTO"
            # Si on a trouvé une marque, on ne la met pas dans "Divers"
            if prefixe_marque != "CAMERA" and prefixe_marque != "PHOTO":
                return {"dossier_base": dossier_racine, "prefixe": prefixe_marque, "renommer": True, "classer_par_date": True}
            return {"dossier_base": f"{dossier_racine}/Divers", "prefixe": "PHOTO", "renommer": True, "classer_par_date": True}

def calculer_chemin_cible_avec_doublons(dossier_destination_base: Path, fichier_source: Path, date_prise: datetime, categorie: dict) -> tuple[str, Path, bool]:
    """
    Calcule le nouveau nom, le chemin cible, et indique si le fichier est un doublon exact déjà présent.
    Si le nom est pris mais le fichier est différent, tente d'ajouter les secondes, puis incrémente le compteur (_1, _2).
    """
    # Sous-classement par année et mois pour les photos
    if categorie["classer_par_date"]:
        annee = date_prise.strftime("%Y")
        mois = date_prise.strftime("%m")
        dossier_cible = dossier_destination_base / categorie["dossier_base"] / annee / mois
    else:
        dossier_cible = dossier_destination_base / categorie["dossier_base"]

        # Création virtuelle du dossier cible (sera réellement créé lors de la copie)
    suffixe = fichier_source.suffix

    if categorie["renommer"]:
        date_str = date_prise.strftime("%Y%m%d_%H%M")
        nouveau_nom_base = f"{categorie['prefixe']}_{date_str}"
        nouveau_nom = f"{nouveau_nom_base}{suffixe}"
    else:
        nouveau_nom_base = fichier_source.stem
        nouveau_nom = fichier_source.name

    chemin_cible = dossier_cible / nouveau_nom

    compteur_doublon = 1
    est_doublon = False
    a_ajoute_secondes = False

    while chemin_cible.exists():
        # Si le fichier existe, on vérifie si c'est strictement le même (taille identique)
        if fichiers_identiques(fichier_source, chemin_cible):
            est_doublon = True
            logger.info(f"Doublon exact détecté sur disque : {fichier_source.name} (Taille: {fichier_source.stat().st_size} octets)")
            break

        # Si c'est un fichier différent (même minute), on ajoute d'abord les secondes si on renomme
        if categorie["renommer"] and not a_ajoute_secondes:
            date_str_avec_sec = date_prise.strftime("%Y%m%d_%H%M%S")
            nouveau_nom_base = f"{categorie['prefixe']}_{date_str_avec_sec}"
            a_ajoute_secondes = True
            logger.debug(f"Conflit de nom minute pour {fichier_source.name}, ajout des secondes : {nouveau_nom_base}")
        else:
            # Si les secondes sont déjà ajoutées et qu'il y a ENCORE conflit (rafale photo par ex), on ajoute _1, _2
            # On cherche s'il y a un "_" suivi d'un ou deux chiffres à la toute fin de la chaîne pour l'isoler proprement
            nouveau_nom_base = re.sub(r'_\d+$', '', nouveau_nom_base)
            nouveau_nom_base = f"{nouveau_nom_base}_{compteur_doublon}"
            compteur_doublon += 1
            logger.debug(f"Conflit de nom seconde pour {fichier_source.name}, ajout d'un index : {nouveau_nom_base}")

        nouveau_nom = f"{nouveau_nom_base}{suffixe}"
        chemin_cible = dossier_cible / nouveau_nom

    return nouveau_nom, chemin_cible, est_doublon

def trouver_fichiers_medias(dossiers_sources: list[str], dossier_destination: str) -> list[dict]:
    """
    Parcourt une liste de dossiers sources pour trouver tous les fichiers médias (photos & vidéos).
    Catégorise les fichiers et calcule leur dossier de destination.
    """
    fichiers_trouves = []
    chemin_dest = Path(dossier_destination)

    logger.info(f"--- DÉMARRAGE D'UN NOUVEAU SCAN ---")
    logger.info(f"Dossiers sources : {dossiers_sources}")
    logger.info(f"Dossier destination : {dossier_destination}")

    # Dictionnaire temporaire (en mémoire) pour tracker les futurs chemins cibles calculés
    # durant ce scan précis. Clé : chemin_cible string, Valeur : info du fichier original
    chemins_cibles_alloues_ce_scan = {}

    for dossier_source in dossiers_sources:
        chemin_dossier = Path(dossier_source)
        if not chemin_dossier.exists() or not chemin_dossier.is_dir():
            continue

        for chemin_fichier in chemin_dossier.rglob("*"):
            if not chemin_fichier.is_file():
                continue

            ext = chemin_fichier.suffix.lower()
            est_video = ext in EXTENSIONS_VIDEO
            est_photo = ext in EXTENSIONS_PHOTO

            # On détermine si la photo est un fichier RAW pour le classement spécifique
            est_raw = ext in {".raw", ".cr2", ".cr3", ".nef", ".arw", ".dng", ".orf", ".rw2"}

            if est_video or est_photo:
                nom_fichier = chemin_fichier.name

                # On identifie la catégorie du média
                categorie = identifier_categorie_media(nom_fichier, est_video, est_raw, chemin_fichier)

                date_prise = obtenir_date_prise_de_vue(chemin_fichier)

                                # Calcul initial du chemin
                nouveau_nom, chemin_cible, est_doublon = calculer_chemin_cible_avec_doublons(chemin_dest, chemin_fichier, date_prise, categorie)

                                # --- ANTI-COLLISION EN MÉMOIRE (INTRA-SCAN) ---
                if not est_doublon:
                    a_ajoute_secondes_mem = False
                    compteur_memoire = 1

                    while str(chemin_cible) in chemins_cibles_alloues_ce_scan:
                        autre_fichier = chemins_cibles_alloues_ce_scan[str(chemin_cible)]
                        if fichiers_identiques(chemin_fichier, autre_fichier):
                            est_doublon = True
                            logger.info(f"Doublon exact détecté en mémoire (intra-scan) : {chemin_fichier.name}")
                            break
                
                        # Résolution de la collision en mémoire : on essaie d'ajouter les secondes d'abord
                        if categorie["renommer"] and not a_ajoute_secondes_mem:
                            date_str_avec_sec = date_prise.strftime("%Y%m%d_%H%M%S")
                            nouveau_nom_base_mem = f"{categorie['prefixe']}_{date_str_avec_sec}"
                            a_ajoute_secondes_mem = True
                            logger.debug(f"Collision mémoire (minute) pour {chemin_fichier.name}, ajout secondes : {nouveau_nom_base_mem}")
                        else:
                            # Si on a déjà mis les secondes (rafale) ou qu'on ne renomme pas, on ajoute _1
                            # On se base sur le nom actuel (celui calculé avec secondes potentiellement)
                            # On retire le suffixe incrémental s'il y en a déjà un
                            # On utilise le nom de base en mémoire courant (qui a déjà les secondes)
                            nom_actuel_sans_ext = nouveau_nom.rsplit('.', 1)[0]
                            nom_sans_compteur = re.sub(r'_\d+$', '', nom_actuel_sans_ext)

                            nouveau_nom_base_mem = f"{nom_sans_compteur}_{compteur_memoire}"
                            compteur_memoire += 1
                            logger.debug(f"Collision mémoire (seconde) pour {chemin_fichier.name}, ajout index : {nouveau_nom_base_mem}")

                        nouveau_nom = f"{nouveau_nom_base_mem}{chemin_fichier.suffix}"
                        chemin_cible = chemin_cible.parent / nouveau_nom

                if not est_doublon:
                    chemins_cibles_alloues_ce_scan[str(chemin_cible)] = chemin_fichier

                # Formatage de la catégorie pour l'affichage (ex: "Images/RAW/2023/11")
                categorie_affichage = categorie["dossier_base"]
                if categorie.get("classer_par_date"):
                    categorie_affichage = f"{categorie_affichage}/{date_prise.strftime('%Y')}/{date_prise.strftime('%m')}"
                
                fichiers_trouves.append({
                    "selectionne": not est_doublon,
                    "est_doublon": est_doublon,
                    "type": "Vidéo" if est_video else ("RAW" if est_raw else "Photo JPG"),
                    "categorie": categorie_affichage,
                    "chemin_complet": chemin_fichier,
                    "nom_original": nom_fichier,
                    "dossier_source": str(chemin_dossier),
                    "date_prise_vue": date_prise,
                    "nouveau_nom": nouveau_nom,
                    "chemin_cible": str(chemin_cible),
                    "taille_go": chemin_fichier.stat().st_size / (1024 ** 3)
                })
                    
    logger.info(f"Fin du scan : {len(fichiers_trouves)} médias identifiés.")
    return fichiers_trouves

