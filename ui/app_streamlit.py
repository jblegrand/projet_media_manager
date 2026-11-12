import streamlit as st
import tkinter as tk
from tkinter import filedialog
import os
import sys

# Ajout du dossier racine au PATH pour les imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.scanner import trouver_fichiers_dji

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
            st.success("Simulation lancée avec succès !")
            st.write(f"**Sources à analyser ({len(st.session_state.sources_list)}) :**")
            for s in st.session_state.sources_list:
                st.write(f"- {s}")
            st.write(f"**Destination :** {dest}")
            
            st.markdown("---")
            st.subheader("🔍 Analyse des fichiers en cours...")
            
            with st.spinner("⏳ Traitement en cours... Veuillez patienter pendant la recherche et le calcul des nouveaux noms."):
                fichiers_dji = trouver_fichiers_dji(st.session_state.sources_list, dest)
            
            if not fichiers_dji:
                st.info("Aucun fichier vidéo DJI (.mp4, .mov) trouvé dans les dossiers sources.")
            else:
                st.write(f"**{len(fichiers_dji)} fichiers DJI identifiés.**")
                
                # Affichage des fichiers trouvés sous forme de tableau complet sans ascenseur vertical si possible
                data_affichage = []
                for f in fichiers_dji:
                    data_affichage.append({
                        "Nom Original": f["nom_original"],
                        "Date de Prise": f["date_prise_vue"].strftime("%d/%m/%Y %H:%M"),
                        "Nouveau Nom": f["nouveau_nom"],
                        "Dossier Cible": f["chemin_cible"],
                        "Dossier Source": os.path.basename(f["dossier_source"])
                    })
                
                # height configuré pour afficher tout le tableau sans scroller verticalement (environ 35px par ligne + 40px header)
                hauteur_tableau = min(35 * len(data_affichage) + 40, 800)
                st.dataframe(data_affichage, use_container_width=True, height=hauteur_tableau)