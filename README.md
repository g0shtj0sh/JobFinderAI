# 🚀 JobFinderAI

**L'interface web universelle pour rechercher, filtrer et suivre toutes vos offres d'emploi et d'alternance, partout, en un clic !**

---

[![Streamlit](https://img.shields.io/badge/Streamlit-Cloud-red?logo=streamlit)](https://streamlit.io/) [![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://www.python.org/) [![JobSpy](https://img.shields.io/badge/Powered%20by-JobSpy-green)](https://github.com/speedyapply/JobSpy)

---

## ✨ Présentation

**JobFinderAI** est une application web open source qui centralise la recherche d'emploi et d'alternance sur toutes les grandes plateformes (Indeed, LinkedIn, Google Jobs...) grâce à la puissance de la librairie [JobSpy](https://github.com/speedyapply/JobSpy).

- Scraping automatique multi-plateforme
- Filtres avancés (statut, entreprise, ville, date, source, mots-clés...)
- Suivi de candidature (statut, relance, etc.)
- Calcul d'itinéraire domicile → offre (OpenRouteService)
- Gestion et export/import de vos paramètres de recherche
- Interface moderne, responsive, 100% personnalisable

---

## 🖥️ Démo

*Ajoutez ici un screenshot ou un GIF de l'interface pour maximiser l'impact !*

---

## 🚀 Fonctionnalités principales

- **Recherche automatisée** sur Indeed, LinkedIn, Google Jobs (et extensible)
- **Base de données locale** (SQLite) pour stocker toutes les offres et leur statut
- **Filtres puissants** : statut, entreprise, ville, date, source, mots-clés, type de poste, distance, etc.
- **Suivi de candidature** : changez le statut, relancez, archivez
- **Calcul d'itinéraire** : temps de trajet estimé entre votre adresse et chaque offre (OpenRouteService, clé gratuite)
- **Gestion des paramètres** : sauvegarde, export, import, réinitialisation
- **Déploiement facile** sur [Streamlit Cloud](https://streamlit.io/cloud) ou en local

---

## ⚡ Installation locale

1. **Clonez le repo**
   ```bash
   git clone https://github.com/votre-utilisateur/JobFinderAI.git
   cd JobFinderAI
   ```
2. **Installez les dépendances**
   ```bash
   pip install -r requirements.txt
   ```
3. **Lancez l'application**
   ```bash
   streamlit run main.py
   ```
4. Ouvrez [http://localhost:8501](http://localhost:8501) dans votre navigateur !

---

## ☁️ Déploiement sur Streamlit Cloud

1. Poussez ce repo sur votre propre GitHub
2. Rendez-vous sur [https://streamlit.io/cloud](https://streamlit.io/cloud) et connectez votre repo
3. Déployez en un clic !

---

## 🔑 Configuration OpenRouteService (itinéraire)

Pour activer le calcul d'itinéraire, créez un compte gratuit sur [openrouteservice.org](https://openrouteservice.org/sign-up/) et récupérez votre clé API. Renseignez-la dans la barre latérale de l'application.

---

## 🛠️ Technologies utilisées
- [JobSpy](https://github.com/speedyapply/JobSpy) (scraping multi-plateforme)
- [Streamlit](https://streamlit.io/) (interface web)
- [SQLite](https://www.sqlite.org/index.html) (base locale)
- [OpenRouteService](https://openrouteservice.org/) (itinéraire)
- [Pandas](https://pandas.pydata.org/) (dataframe)

---

## 🙏 Remerciements
- Ce projet n'existerait pas sans la librairie [JobSpy](https://github.com/speedyapply/JobSpy) ❤️
- Merci à la communauté open source !

---

## 📣 Contribuer / Questions
- Suggestions, bugs, idées ? Ouvrez une issue ou une pull request !
- Pour toute question, contactez-moi via GitHub.

---

**JobFinderAI** – Centralisez, automatisez, trouvez votre job ou alternance de rêve !
