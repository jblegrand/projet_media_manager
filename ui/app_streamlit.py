import streamlit as st
import tkinter as tk
from tkinter import filedialog
import os
import sys
import pandas as pd

# Ajout du dossier racine au PATH pour les imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.scanner import trouver_fichiers_dji
from core.copier import deplacer_fichiers_securise, format_size, supprimer_fichiers_sources

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
if "dest_list" not in st.session_state:
    st.session_state.dest_list = []  # Limité à un seul élément
if "simulation_run" not in st.session_state:
    st.session_state.simulation_run = False
if "fichiers_dji" not in st.session_state:
    st.session_state.fichiers_dji = []

st.header("1. Paramètres de saisie")

# --- Dossiers Sources (Multiples) ---
st.subheader("Dossiers Sources (Cartes SD / Répertoires)")

if st.button("➕ Ajouter un dossier source", key="btn_add_src"):
    chosen_dir = select_folder("Sélectionner un dossier source")
    if chosen_dir:
        norm_chosen = os.path.normpath(chosen_dir)
        # Vérification si le dossier est déjà la destination
        is_dest = any(os.path.normpath(d) == norm_chosen for d in st.session_state.dest_list)
        if is_dest:
            st.error("Ce dossier ne peut pas être une source car il est déjà défini comme destination.")
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

# --- Dossier de Destination (Unique, même ergonomie avec bouton grisé) ---
st.subheader("Dossier de Destination (Cible unique)")

# Le bouton est désactivé s'il y a déjà un dossier de destination
has_dest = len(st.session_state.dest_list) > 0

if st.button("➕ Ajouter un dossier destination", key="btn_add_dest", disabled=has_dest):
    chosen_dir = select_folder("Sélectionner le dossier de destination")
    if chosen_dir:
        norm_chosen = os.path.normpath(chosen_dir)
        # Vérification si le dossier est déjà dans les sources
        is_source = any(os.path.normpath(s) == norm_chosen for s in st.session_state.sources_list)
        if is_source:
            st.error("Le dossier de destination ne peut pas être l'un des dossiers sources.")
        else:
            st.session_state.dest_list = [chosen_dir]
            st.rerun()

# Affichage de la destination sélectionnée avec option de suppression
if st.session_state.dest_list:
    for idx, dst in enumerate(st.session_state.dest_list):
        cols = st.columns([6, 1])
        with cols[0]:
            st.text(f"📁 {dst}")
        with cols[1]:
            if st.button("❌", key=f"del_dest_{idx}"):
                st.session_state.dest_list.pop(idx)
                st.rerun()
else:
    st.info("Aucun dossier de destination sélectionné pour le moment.")

st.markdown("---")

# --- Bouton de simulation ---
if st.button("Lancer la simulation (Dry-Run)", type="primary"):
    if not st.session_state.sources_list:
        st.warning("Veuillez renseigner au moins un dossier source.")
    elif not st.session_state.dest_list:
        st.warning("Veuillez renseigner le dossier de destination.")
    else:
        dest = st.session_state.dest_list[0]
        norm_dest = os.path.normpath(dest)
        conflict = any(os.path.normpath(s) == norm_dest for s in st.session_state.sources_list)
        
        if conflict:
            st.error("❌ Erreur : Le dossier de destination ne peut pas être identique à l'un des dossiers sources.")
        else:
            with st.spinner("⏳ Traitement en cours... Veuillez patienter pendant la recherche et le calcul des nouveaux noms."):
                # On stocke le résultat dans la session pour qu'il persiste après un rerun
                st.session_state.fichiers_dji = trouver_fichiers_dji(st.session_state.sources_list, dest)
                st.session_state.simulation_run = True

# --- Affichage des résultats si la simulation a été lancée ---
if st.session_state.simulation_run:
    dest = st.session_state.dest_list[0]
    
    st.success("Simulation lancée avec succès !")
    st.write(f"**Sources à analyser ({len(st.session_state.sources_list)}) :**")
    for s in st.session_state.sources_list:
        st.write(f"- {s}")
    st.write(f"**Destination :** {dest}")
    
    st.markdown("---")
    st.subheader("🔍 Analyse des fichiers en cours...")
    
    if not st.session_state.fichiers_dji:
        st.info("Aucun fichier vidéo DJI (.mp4, .mov) trouvé dans les dossiers sources.")
    else:
                # Calcul de la taille directement depuis le chemin du fichier
        # On vérifie d'abord que le fichier source existe toujours (cas où on annule après une copie réussie)
        fichiers_existants = [f for f in st.session_state.fichiers_dji if f["chemin_complet"].exists()]
        
        taille_totale_go = round(sum(f["chemin_complet"].stat().st_size / (1024 ** 3) for f in fichiers_existants), 2)
        
        # Formatage spécifique
        if taille_totale_go == 0.0 and fichiers_existants:
            taille_affichage = "< 0.01"
        else:
            taille_affichage = str(taille_totale_go)
            
        st.write(f"**{len(st.session_state.fichiers_dji)} fichiers DJI identifiés, soit {taille_affichage} Go de vidéo à déplacer.**")
        
                # --- Boutons pour tout sélectionner / désélectionner ---
        col_sel1, col_sel2, _ = st.columns([2, 2, 6])
        with col_sel1:
            if st.button("☑️ Tout sélectionner", use_container_width=True):
                if "data_affichage" in st.session_state:
                    st.session_state.data_affichage["Sélection"] = True
                    st.rerun()
        with col_sel2:
            if st.button("🔲 Tout désélectionner", use_container_width=True):
                if "data_affichage" in st.session_state:
                    st.session_state.data_affichage["Sélection"] = False
                    st.rerun()
                    
        # --- Gestion de l'éditeur de données (checkbox) ---
        # On crée le dataframe initial à partir de la session si ce n'est pas déjà fait
        # En utilisant un dataframe Pandas pour que le composant data_editor l'interprète correctement et retourne un DataFrame
        if "data_affichage" not in st.session_state:
            data = []
            for f in st.session_state.fichiers_dji:
                data.append({
                    "Sélection": f.get("selectionne", True),
                    "Nom Original": f["nom_original"],
                    "Date de Prise": f["date_prise_vue"].strftime("%d/%m/%Y %H:%M"),
                    "Nouveau Nom": f["nouveau_nom"],
                    "Dossier Cible": f["chemin_cible"],
                    "Dossier Source": os.path.basename(f["dossier_source"])
                })
            st.session_state.data_affichage = pd.DataFrame(data)
            
        hauteur_tableau = min(35 * len(st.session_state.data_affichage) + 40, 800)
        st.session_state.edited_df = st.data_editor(
                    st.session_state.data_affichage, 
                    use_container_width=True, 
                    height=hauteur_tableau,
                    hide_index=True,
                    column_config={
                        "Sélection": st.column_config.CheckboxColumn(
                            "Sélection",
                            help="Sélectionnez les vidéos à déplacer",
                            default=True,
                        ),
                        "Nom Original": st.column_config.Column(disabled=True),
                        "Date de Prise": st.column_config.Column(disabled=True),
                        "Nouveau Nom": st.column_config.Column(disabled=True),
                        "Dossier Cible": st.column_config.Column(disabled=True),
                        "Dossier Source": st.column_config.Column(disabled=True)
                    }
                )

        st.markdown("---")
        st.subheader("🚀 2. Validation et Déplacement")

        # Récupération des fichiers sélectionnés via l'éditeur
        # On vérifie d'abord que edited_df existe bien et a la même longueur que fichiers_dji
        if "edited_df" in st.session_state and len(st.session_state.edited_df) == len(st.session_state.fichiers_dji):
            fichiers_a_deplacer = [
                f for i, f in enumerate(st.session_state.fichiers_dji) 
                if st.session_state.edited_df.iloc[i]["Sélection"]
            ]
        else:
            # Sécurité fallback si l'éditeur n'a pas encore mis à jour l'état
            fichiers_a_deplacer = [f for f in st.session_state.fichiers_dji if f.get("selectionne", True)]

        if not fichiers_a_deplacer:
            st.warning("Veuillez sélectionner au moins un fichier à déplacer dans le tableau ci-dessus.")
        else:
            # Phase 2A : Interface de copie
            if not st.session_state.get("copie_terminee", False):
                col1, col2 = st.columns([2, 8])
                with col1:
                    # Le bouton déclenche l'affichage de l'interface de copie
                    if st.button("✅ Valider et Copier", type="primary", use_container_width=True):
                        st.session_state.processus_en_cours = True
                
                with col2:
                    # Bouton permettant d'annuler (et donc nettoyer)
                    if st.session_state.get("processus_en_cours", False):
                        if st.button("🛑 Annuler et tout effacer", type="secondary", use_container_width=True):
                            st.session_state.processus_en_cours = False
                            st.rerun()

                if st.session_state.get("processus_en_cours", False):
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
                    if st.button("🗑️ Supprimer les sources originales", type="primary", use_container_width=True):
                        supprimer_fichiers_sources(fichiers_a_deplacer)
                        st.session_state.simulation_run = False
                        st.session_state.copie_terminee = False
                        del st.session_state.data_affichage
                        st.success("Fichiers sources supprimés !")
                        st.rerun()
                        
                with col_sup2:
                    if st.button("🏠 Conserver les sources et retourner à l'accueil", use_container_width=True):
                        st.session_state.simulation_run = False
                        st.session_state.copie_terminee = False
                        del st.session_state.data_affichage
                        st.rerun()