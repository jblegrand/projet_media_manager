import streamlit as st
import tkinter as tk
from tkinter import filedialog

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

# --- Initialisation des chemins dans la session ---
if "source_val" not in st.session_state:
    st.session_state.source_val = ""
if "dest_val" not in st.session_state:
    st.session_state.dest_val = ""

st.header("1. Paramètres de saisie")

# --- Dossier Source ---
col1, col2 = st.columns([4, 1], vertical_alignment="bottom")
with col1:
    # On récupère la valeur depuis la session
    source_dir = st.text_input("Dossier Source (ex: Carte SD Drone)", value=st.session_state.source_val)
    if source_dir != st.session_state.source_val:
        st.session_state.source_val = source_dir
with col2:
    if st.button("📁 Parcourir", key="btn_src", use_container_width=True):
        chosen_dir = select_folder("Sélectionner le dossier source")
        if chosen_dir:
            st.session_state.source_val = chosen_dir
            st.rerun()

# --- Dossier Destination ---
col3, col4 = st.columns([4, 1], vertical_alignment="bottom")
with col3:
    dest_dir = st.text_input("Dossier de Destination (Cible)", value=st.session_state.dest_val)
    if dest_dir != st.session_state.dest_val:
        st.session_state.dest_val = dest_dir
with col4:
    if st.button("📁 Parcourir", key="btn_dst", use_container_width=True):
        chosen_dir = select_folder("Sélectionner le dossier de destination")
        if chosen_dir:
            st.session_state.dest_val = chosen_dir
            st.rerun()

st.write("")

# Bouton de simulation
if st.button("Lancer la simulation (Dry-Run)", type="primary"):
    if st.session_state.source_val and st.session_state.dest_val:
        st.success("Simulation lancée avec succès !")
        st.write(f"**Source :** {st.session_state.source_val}")
        st.write(f"**Destination :** {st.session_state.dest_val}")
    else:
        st.warning("Veuillez renseigner à la fois le dossier source et le dossier de destination.")