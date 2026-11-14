# Gestionnaire de Médias & Tri Sécurisé

Application modulaire en Python conçue pour trier, vérifier et organiser automatiquement les fichiers médias (notamment les vidéos lourdes de drones DJI) par date de prise de vue, de manière hautement sécurisée.

## Fonctionnalités Principales

- **Tri Intelligent & Anti-Doublon :** Analyse automatique des répertoires sources pour isoler les vidéos DJI (`.mp4`, `.mov`). Détection stricte des doublons à l'octet près.
- **Nommage Automatisé :** Renommage automatique des fichiers en fonction de leur date de prise de vue (`DJI_YYYYMMDD_HHMM.ext`), avec gestion intelligente des conflits de noms (suffixe `_1`, `_2`).
- **Dry-Run & Sélection :** Simulation du traitement dans un tableau interactif permettant de sélectionner/désélectionner précisément les fichiers à traiter, avec calcul de la volumétrie réelle. Les doublons sont mis en surbrillance (rouge pastel) et décochés par défaut.
- **Copie Ultra-Sécurisée (Battle Tested) :** 
  - *Pre-flight check* : Vérification de l'espace disque cible avant démarrage.
  - *Opération Atomique* : Copie via des fichiers temporaires (`.part`) pour éviter la corruption en cas de coupure (arrachage de la carte SD).
  - *RAM Safe* : Transfert par blocs de 10 Mo.
- **Intégrité Garantie :** Calcul du hash SHA-256 à la volée sur la source et la destination pour garantir 100% d'intégrité.
- **Workflow en Deux Temps & Nettoyage :** La copie est d'abord effectuée. Ensuite, l'utilisateur a le choix (via boutons explicites) de supprimer les fichiers sources originaux de sa carte SD, ou de nettoyer spécifiquement les doublons inutiles.

## Architecture du Projet

Le projet suit une approche modulaire pour séparer strictement la logique métier de l'interface utilisateur :

- `core/` : Moteur logique (indépendant de l'IHM).
  - `scanner.py` : Recherche des fichiers, extraction des métadonnées (`hachoir`) et calcul des futurs noms.
  - `copier.py` : Logique de transfert sécurisé, hachage SHA-256 par blocs et suppression contrôlée.
- `ui/` : Couche d'interface utilisateur graphique (développée avec `Streamlit`).
  - `app_streamlit.py` : Dashboard principal interactif.

## Prérequis

- Python 3.15+

## Installation et Lancement

1. Cloner ou initialiser le projet.
2. Installer les dépendances nécessaires (`streamlit`, `pandas`, `hachoir`) :
   ```powershell
   py -m pip install streamlit pandas hachoir
   ```
3. Lancer l'interface web depuis le terminal intégré de VS Code :
   - Assurez-vous d'être à la racine du projet (`projet_media_manager`).
   - Exécutez la commande suivante :
     ```powershell
     py -m streamlit run ui/app_streamlit.py
     ```
   - Une fenêtre de navigateur s'ouvrira automatiquement à l'adresse `http://localhost:8501`.

## Philosophie et Workflow

Ce projet a été développé en mode Agile. Les interventions sur le code doivent impérativement respecter la séparation des responsabilités entre `core/` (logique bas niveau, manipulation disque) et `ui/` (interfaces, session Streamlit, barres de progression).