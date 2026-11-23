import streamlit as st
import tkinter as tk
from tkinter import filedialog
import os
import sys
import pandas as pd

# Ajout du dossier racine au PATH pour les imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.scanner import trouver_fichiers_medias
from core.copier import deplacer_fichiers_securise, format_size, supprimer_fichiers_sources
from core.logger import get_logger

logger = get_logger()

def select_folder(title):
    """Ouvre une boîte de dialogue Windows pour sélectionner un dossier"""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder_path = filedialog.askdirectory(title=title)
    root.destroy()
    return folder_path

# Configuration de la page
st.set_page_config(page_title="Gestionnaire de Médias", page_icon="🚁", layout="wide")

# Personnalisation du style CSS pour ajuster la disposition
st.markdown("""
    <style>
    /* Ajustement des marges et de la largeur maximale de l'application */
    .block-container {
        max-width: 1200px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        margin-left: 0 !important; /* Aligne le contenu à gauche sur les grands écrans */
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚁 Gestionnaire de Médias & Tri Sécurisé")
st.write("Bienvenue dans votre interface de tri modulaire.")

# --- Initialisation de l'état de session ---
if "sources_list" not in st.session_state:
    st.session_state.sources_list = []
if "simulation_run" not in st.session_state:
    st.session_state.simulation_run = False
if "fichiers_medias" not in st.session_state:
    st.session_state.fichiers_medias = []

st.header("1. Paramètres de saisie")

# --- Dossiers Sources (Multiples) ---
st.subheader("Dossiers Sources (Cartes SD / Répertoires)")

if st.button("➕ Ajouter un dossier source", key="btn_add_src"):
    chosen_dir = select_folder("Sélectionner un dossier source")
    if chosen_dir:
        norm_chosen = os.path.normpath(chosen_dir)
        # Vérification si le dossier est sur le disque D: (notre destination globale)
        if norm_chosen.upper().startswith("D:\\"):
            st.error("Ce dossier ne peut pas être une source car il est situé sur le disque de destination global (D:\\).")
        elif norm_chosen not in [os.path.normpath(s) for s in st.session_state.sources_list]:
            st.session_state.sources_list.append(chosen_dir)
            st.rerun()

# Affichage de la liste des sources
if st.session_state.sources_list:
    for idx, src in enumerate(st.session_state.sources_list):
        cols = st.columns([6, 1])
        with cols[0]:
            st.text(f"📁 {src}")
        with cols[1]:
            if st.button("❌", key=f"del_src_{idx}"):
                st.session_state.sources_list.pop(idx)
                st.rerun()
else:
    st.info("Aucun dossier source sélectionné pour le moment.")

st.markdown("---")

# --- Bouton de simulation ---
if st.button("Lancer la simulation (Dry-Run)", type="primary"):
    if not st.session_state.sources_list:
        st.warning("Veuillez renseigner au moins un dossier source.")
    else:
        # La destination de base est désormais fixée en dur à D:
        dest_base = "D:\\"
        norm_dest_base = os.path.normpath(dest_base)
        
        # On vérifie qu'on n'essaie pas de scanner D:\ entier pour copier dans D:\, ce qui créerait une boucle infinie
        conflict = False
        for s in st.session_state.sources_list:
            if os.path.normpath(s) == norm_dest_base or os.path.normpath(s).startswith(norm_dest_base + os.sep):
                conflict = True
                break
        
        if conflict:
            st.error("❌ Erreur : Vous ne pouvez pas définir une source située sur le disque de destination (D:\\) pour éviter les conflits de copie.")
        else:
            with st.spinner("⏳ Traitement en cours... Veuillez patienter pendant la recherche et le tri des médias."):
                # On stocke le résultat dans la session pour qu'il persiste après un rerun
                st.session_state.fichiers_medias = trouver_fichiers_medias(st.session_state.sources_list, dest_base)
                st.session_state.simulation_run = True

# --- Affichage des résultats si la simulation a été lancée ---
if st.session_state.simulation_run:
    dest_base = "D:\\"
    
    st.success("Simulation lancée avec succès !")
    st.write(f"**Sources à analyser ({len(st.session_state.sources_list)}) :**")
    for s in st.session_state.sources_list:
        st.write(f"- {s}")
    st.write(f"**Disque Destination (Root) :** {dest_base}")
    
    st.markdown("---")
    st.subheader("🔍 Analyse des fichiers en cours...")
    
        # Injection d'un petit script Javascript pour faire scroller automatiquement la page
    # jusqu'à cette section une fois l'analyse terminée.
    # On utilise st.html (nouveau composant Streamlit) au lieu de st.components.v1.html/iframe qui sont dépréciés
    st.html(
        """
        <script>
            // Un délai pour s'assurer que Streamlit a fini de dessiner les éléments
            setTimeout(function() {
                window.parent.document.querySelector('h3').scrollIntoView({behavior: 'smooth'});
            }, 500);
        </script>
        """
    )
    
    if not st.session_state.fichiers_medias:
        st.info("Aucun fichier média (photo ou vidéo) trouvé dans les dossiers sources.")
    else:
        # Calcul de la taille directement depuis le chemin du fichier
        # On vérifie d'abord que le fichier source existe toujours (cas où on annule après une copie réussie)
        fichiers_existants = [f for f in st.session_state.fichiers_medias if f["chemin_complet"].exists()]
        
        taille_totale_go = round(sum(f["chemin_complet"].stat().st_size / (1024 ** 3) for f in fichiers_existants), 2)
        
        # Formatage spécifique
        if taille_totale_go == 0.0 and fichiers_existants:
            taille_affichage = "< 0.01"
        else:
            taille_affichage = str(taille_totale_go)
            
        st.write(f"**{len(st.session_state.fichiers_medias)} médias identifiés, soit {taille_affichage} Go à trier.**")
        
                # --- Boutons pour tout sélectionner / désélectionner ---
        col_sel1, col_sel2, _ = st.columns([2, 2, 6])
        with col_sel1:
            if st.button("☑️ Tout sélectionner", width='stretch'):
                if "data_affichage" in st.session_state:
                    st.session_state.data_affichage["Sélection"] = True
                    st.rerun()
        with col_sel2:
            if st.button("🔲 Tout désélectionner", width='stretch'):
                if "data_affichage" in st.session_state:
                    st.session_state.data_affichage["Sélection"] = False
                    st.rerun()
                    
        # --- Gestion de l'éditeur de données (checkbox) ---
        # On crée le dataframe initial à partir de la session si ce n'est pas déjà fait
        # En utilisant un dataframe Pandas pour que le composant data_editor l'interprète correctement et retourne un DataFrame
        if "data_affichage" not in st.session_state:
            data = []
            for f in st.session_state.fichiers_medias:
                # Ajout d'une mention dans le statut si c'est un doublon
                statut_doublon = "⚠️ Doublon" if f.get("est_doublon", False) else "Nouveau"
                
                # Formatage du dossier destination complet pour une meilleure visibilité
                dossier_cible = f.get("categorie", "")
                
                data.append({
                    "Sélection": f.get("selectionne", True),
                    "Statut": statut_doublon,
                    "Type": f["type"],
                    "Nom Original": f["nom_original"],
                    "Date de Prise": f["date_prise_vue"].strftime("%d/%m/%Y %H:%M"),
                    "Nouveau Nom": f["nouveau_nom"],
                    "Dossier Destination": dossier_cible
                })
            st.session_state.data_affichage = pd.DataFrame(data)
            
            # --- Tri automatique du tableau ---
            # 1. Par Statut : "⚠️ Doublon" vient avant "Nouveau"
            # 2. Par Type : Photo puis Vidéo
            # 3. Par Dossier Destination
            st.session_state.data_affichage = st.session_state.data_affichage.sort_values(by=["Statut", "Type", "Dossier Destination", "Date de Prise"], ascending=[False, True, True, True])
            
            # --- SYNCHRONISATION CRITIQUE ---
            # Pour que les index de notre DataFrame trié correspondent aux index de la liste brute st.session_state.fichiers_medias
            # que l'on va passer à la fonction de copie, il faut absolument trier cette liste source 
            # dans le MEME ORDRE que le tableau d'affichage !
            st.session_state.fichiers_medias.sort(
                key=lambda f: (
                    not f.get("est_doublon", False), # False (0) d'abord pour les doublons
                    f["type"],
                    f.get("categorie", ""),
                    f["date_prise_vue"]
                )
            )
            
            st.session_state.data_affichage = st.session_state.data_affichage.reset_index(drop=True)
            
        # Hauteur calculée pour s'assurer qu'aucun ascenseur interne n'apparaisse.
        hauteur_tableau = (35 * len(st.session_state.data_affichage)) + 40
        
        # Fonction de style pour mettre en surbrillance les lignes "Doublon détecté"
        def style_doublons(row):
            if row["Statut"] == "⚠️ Doublon":
                return ['background-color: #ffe6e6'] * len(row) # Rouge pastel/orange clair
            return [''] * len(row)
            
        styled_df = st.session_state.data_affichage.style.apply(style_doublons, axis=1)

        st.session_state.edited_df = st.data_editor(
                    styled_df, 
                    width='stretch',
                    height=hauteur_tableau,
                    hide_index=True,
                    column_config={
                        "Sélection": st.column_config.CheckboxColumn(
                            "Sélection",
                            help="Sélectionnez les médias à déplacer",
                            default=True,
                            width="small"
                        ),
                        "Statut": st.column_config.Column(disabled=True, width="small"),
                        "Type": st.column_config.Column(disabled=True, width="small"),
                        "Nom Original": st.column_config.Column(disabled=True, width="medium"),
                        "Date de Prise": st.column_config.Column(disabled=True, width="medium"),
                        "Nouveau Nom": st.column_config.Column(disabled=True, width="medium"),
                        "Dossier Destination": st.column_config.Column(disabled=True, width="large")
                    }
                )

                # --- Bouton "Nettoyage des doublons à la source" ---
        doublons_existants = [f for f in st.session_state.fichiers_medias if f.get("est_doublon", False)]
        if doublons_existants:
            st.info(f"💡 {len(doublons_existants)} fichier(s) identifié(s) comme déjà sécurisé(s) dans la destination (Doublon).")
            if st.button("🧹 Supprimer uniquement les doublons de la carte SD (Source)"):
                # Affiche une boîte de dialogue native pour confirmer (Dry-run de sécurité)
                if tk.messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer définitivement les {len(doublons_existants)} fichiers doublons de la source ?\nIls sont déjà sécurisés dans votre dossier de destination."):
                    logger.info("Utilisateur a confirmé la suppression des doublons à la source.")
                    supprimer_fichiers_sources(doublons_existants)
                    st.success(f"{len(doublons_existants)} doublon(s) supprimé(s) de la source avec succès !")
                    st.session_state.simulation_run = False
                    del st.session_state.data_affichage
                    st.rerun()

        st.markdown("---")
        st.subheader("🚀 2. Validation et Copie")

        # Récupération des fichiers sélectionnés via l'éditeur
        # On vérifie d'abord que edited_df existe bien et a la même longueur que fichiers_medias
        if "edited_df" in st.session_state and len(st.session_state.edited_df) == len(st.session_state.fichiers_medias):
            fichiers_a_deplacer = [
                f for i, f in enumerate(st.session_state.fichiers_medias) 
                if st.session_state.edited_df.iloc[i]["Sélection"]
            ]
        else:
            # Sécurité fallback si l'éditeur n'a pas encore mis à jour l'état
            fichiers_a_deplacer = [f for f in st.session_state.fichiers_medias if f.get("selectionne", True)]

        if not fichiers_a_deplacer:
            st.warning("Veuillez sélectionner au moins un fichier à déplacer dans le tableau ci-dessus.")
        else:
                        # Phase 2A : Interface de copie
            if not st.session_state.get("copie_terminee", False):
                col1, col2 = st.columns([2, 8])
                with col1:
                    # Le bouton déclenche l'affichage de l'interface de copie
                    if st.button("✅ Valider et Copier", type="primary", width='stretch'):
                        logger.info("Utilisateur a cliqué sur 'Valider et Copier'.")
                        st.session_state.processus_en_cours = True
                
                with col2:
                    # Bouton permettant d'annuler (et donc nettoyer)
                    if st.session_state.get("processus_en_cours", False):
                        if st.button("🛑 Annuler et tout effacer", type="secondary", width='stretch'):
                            logger.info("Utilisateur a cliqué sur 'Annuler et tout effacer'.")
                            st.session_state.processus_en_cours = False
                            st.rerun()

                if st.session_state.get("processus_en_cours", False):
                    st.html(
                        """
                        <script>
                            // Fait descendre la page en bas au lancement de la copie
                            setTimeout(function() {
                                window.parent.document.documentElement.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
                            }, 100);
                        </script>
                        """
                    )
                    
                    st.info("⚠️ Ne fermez pas cette page. La copie est en cours...")
                    
                    progress_bar_globale = st.progress(0, text="Progression totale : 0 %")
                    progress_bar_fichier = st.progress(0, text="Fichier en cours...")
                    status_text = st.empty()

                    def interface_mise_a_jour(nom_fichier, statut, bytes_fichier, total_fichier, bytes_global, total_global):
                        pct_fichier = min(bytes_fichier / total_fichier, 1.0) if total_fichier else 1.0
                        pct_global = min(bytes_global / total_global, 1.0) if total_global else 1.0
                        
                        progress_bar_fichier.progress(
                            pct_fichier, 
                            text=f"Fichier : {nom_fichier} - {format_size(bytes_fichier)} / {format_size(total_fichier)} ({pct_fichier*100:.1f}%)"
                        )
                        progress_bar_globale.progress(
                            pct_global, 
                            text=f"Progression globale : {format_size(bytes_global)} / {format_size(total_global)} ({pct_global*100:.1f}%)"
                        )
                        status_text.text(f"Statut : {statut}")

                    try:
                        deplacer_fichiers_securise(fichiers_a_deplacer, interface_mise_a_jour)
                        st.session_state.processus_en_cours = False
                        st.session_state.copie_terminee = True
                        st.rerun()
                            
                    except Exception as e:
                        st.error(f"❌ Processus interrompu. Les fichiers partiellement copiés lors de cette session ont été nettoyés de la destination. ({str(e)})")
                        st.session_state.processus_en_cours = False
            
            # Phase 2B : Demande de suppression post-copie
            else:
                st.success("🎉 Les fichiers ont été copiés et vérifiés avec succès dans le dossier de destination !")
                st.write("Vous pouvez vérifier les fichiers dans votre dossier cible.")
                
                st.markdown("### 🗑️ Que voulez-vous faire des fichiers d'origine ?")
                
                col_sup1, col_sup2 = st.columns([1, 1])
                
                with col_sup1:
                    if st.button("🗑️ Supprimer les sources originales", type="primary", width='stretch'):
                        logger.info("Utilisateur a demandé la suppression des sources originales post-copie.")
                        supprimer_fichiers_sources(fichiers_a_deplacer)
                        st.session_state.simulation_run = False
                        st.session_state.copie_terminee = False
                        del st.session_state.data_affichage
                        st.success("Fichiers sources supprimés !")
                        st.rerun()
                        
                with col_sup2:
                    if st.button("🏠 Conserver les sources et retourner à l'accueil", width='stretch'):
                        logger.info("Utilisateur a choisi de conserver les sources (Retour accueil).")
                        st.session_state.simulation_run = False
                        st.session_state.copie_terminee = False
                        del st.session_state.data_affichage
                        st.rerun()