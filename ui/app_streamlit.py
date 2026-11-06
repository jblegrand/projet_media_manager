import streamlit as st
import tkinter as tk
from tkinter import filedialog
import os

def select_folder(title):
    """Ouvre une boîte de dialogue Windows pour sélectionner un dossier"""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder_path = filedialog.askdirectory(title=title)
    root.destroy()
    return folder_path

# Configuration de la page
st.set_page_config(page_title="Gestionnaire de Médias", page_icon="🚁", layout="centered")

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
            st.write(f"**Sources à traiter ({len(st.session_state.sources_list)}) :**")
            for s in st.session_state.sources_list:
                st.write(f"- {s}")
            st.write(f"**Destination :** {dest}")