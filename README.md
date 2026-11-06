# Gestionnaire de Médias & Tri Sécurisé

Application modulaire en Python conçue pour trier et organiser automatiquement les fichiers médias (photos, vidéos de drones DJI) par date de manière sécurisée (mode simulation / dry-run).

## Architecture du Projet

Le projet suit une approche modulaire (type micro-services internes) pour séparer la logique métier de l'interface utilisateur :

- `core/` : Moteur logique et extracteur de métadonnées (indépendant de l'IHM).
- `ui/` : Couche interface utilisateur (développée avec Streamlit).

## Prérequis

- Python 3.15+
- Streamlit

## Installation et Lancement

1. Cloner ou initialiser le projet.
2. Installer les dépendances :
   ```powershell
   py -m pip install streamlit