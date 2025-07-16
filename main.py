import streamlit as st
import pandas as pd
import sqlite3
import webbrowser
import json
from datetime import datetime
from jobspy.indeed import Indeed
from jobspy.linkedin import LinkedIn
from jobspy.google import Google
from jobspy.model import ScraperInput, Site, Country, DescriptionFormat, JobType
import requests
import time

# ---------------------- CONFIGURATION ----------------------
DB_PATH = "jobs.sqlite3"
DEFAULT_CONFIG = {
    "keywords": [],
    "location": "",
    "country": "FRANCE",
    "distance": 30,
    "results_per_keyword": 20,
    "days_old": 7
}

# ---------------------- BASE DE DONNÉES ----------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        location TEXT,
        url TEXT UNIQUE,
        date_posted TEXT,
        description TEXT,
        status TEXT DEFAULT 'non candidaté',
        source TEXT
    )''')
    conn.commit()
    conn.close()

def insert_jobs(jobs):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    new_count = 0
    for job in jobs:
        try:
            c.execute('''INSERT INTO jobs (title, company, location, url, date_posted, description, source) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (job['title'], job['company'], job['location'], job['url'], job['date_posted'], job['description'], job['source']))
            new_count += 1
        except sqlite3.IntegrityError:
            continue  # doublon (url unique)
    conn.commit()
    conn.close()
    return new_count

def get_jobs_df():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM jobs", conn)
    conn.close()
    return df

def update_status(job_id, new_status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE jobs SET status = ? WHERE id = ?", (new_status, job_id))
    conn.commit()
    conn.close()

# ---------------------- SCRAPING ----------------------
def jobspy_to_dict(job, source):
    return {
        'title': job.title,
        'company': job.company_name or '',
        'location': job.location.display_location() if job.location else '',
        'url': job.job_url,
        'date_posted': str(job.date_posted) if job.date_posted else '',
        'description': job.description or '',
        'source': source
    }

def scrape_all(keywords, location, country, distance, results_per_keyword, hours_old):
    all_jobs = []
    for kw in keywords:
        # Indeed
        try:
            indeed_scraper = Indeed()
            indeed_input = ScraperInput(
                site_type=[Site.INDEED],
                search_term=kw,
                location=location,
                country=Country[country],
                distance=distance,
                results_wanted=results_per_keyword,
                hours_old=hours_old,
                description_format=DescriptionFormat.MARKDOWN,
            )
            indeed_jobs = indeed_scraper.scrape(indeed_input).jobs
            all_jobs.extend([jobspy_to_dict(j, "Indeed") for j in indeed_jobs])
        except Exception as e:
            print(f"Erreur Indeed: {e}")
        # LinkedIn
        try:
            linkedin_scraper = LinkedIn()
            linkedin_input = ScraperInput(
                site_type=[Site.LINKEDIN],
                search_term=kw,
                location=location,
                country=Country[country],
                distance=distance,
                results_wanted=results_per_keyword,
                hours_old=hours_old,
                description_format=DescriptionFormat.MARKDOWN,
                linkedin_fetch_description=False,
            )
            linkedin_jobs = linkedin_scraper.scrape(linkedin_input).jobs
            all_jobs.extend([jobspy_to_dict(j, "LinkedIn") for j in linkedin_jobs])
        except Exception as e:
            print(f"Erreur LinkedIn: {e}")
        # Google Jobs
        try:
            google_scraper = Google()
            google_input = ScraperInput(
                site_type=[Site.GOOGLE],
                search_term=kw,
                location=location,
                country=Country[country],
                distance=distance,
                results_wanted=results_per_keyword,
                hours_old=hours_old,
                description_format=DescriptionFormat.MARKDOWN,
            )
            google_jobs = google_scraper.scrape(google_input).jobs
            all_jobs.extend([jobspy_to_dict(j, "Google") for j in google_jobs])
        except Exception as e:
            print(f"Erreur Google Jobs: {e}")
    return all_jobs

# ---------------------- ITINÉRAIRE (OpenRouteService) ----------------------
def get_travel_time(api_key, from_address, to_address):
    if not api_key or not from_address or not to_address:
        return None, None
    try:
        # Géocodage des adresses
        url_geocode = "https://api.openrouteservice.org/geocode/search"
        params_from = {"api_key": api_key, "text": from_address}
        params_to = {"api_key": api_key, "text": to_address}
        resp_from = requests.get(url_geocode, params=params_from).json()
        resp_to = requests.get(url_geocode, params=params_to).json()
        coords_from = resp_from["features"][0]["geometry"]["coordinates"]
        coords_to = resp_to["features"][0]["geometry"]["coordinates"]
        # Calcul d'itinéraire
        url_route = "https://api.openrouteservice.org/v2/directions/driving-car"
        params_route = {
            "api_key": api_key,
        }
        body = {
            "coordinates": [coords_from, coords_to]
        }
        resp_route = requests.post(url_route, params=params_route, json=body).json()
        duration = resp_route["features"][0]["properties"]["summary"]["duration"]
        distance = resp_route["features"][0]["properties"]["summary"]["distance"]
        # Conversion
        minutes = int(duration // 60)
        km = round(distance / 1000, 1)
        return minutes, km
    except Exception as e:
        return None, None

# ---------------------- NOMINATIM (OpenStreetMap) ----------------------
def get_company_full_address(company, city, api_key=None):
    """
    Recherche l'adresse complète d'une entreprise via Nominatim (OpenStreetMap).
    """
    if not company or not city:
        return None
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": f"{company}, {city}, France",
            "format": "json",
            "addressdetails": 1,
            "limit": 1
        }
        headers = {"User-Agent": "JobFinderAI/1.0"}
        if api_key:
            params["key"] = api_key
        resp = requests.get(url, params=params, headers=headers)
        time.sleep(1)  # Respecte la politique Nominatim (1 requête/sec)
        data = resp.json()
        if data and len(data) > 0:
            return data[0]["display_name"]
        return None
    except Exception as e:
        return None

# ---------------------- INTERFACE STREAMLIT ----------------------
# CSS pour sidebar fixe et boutons stylés
st.markdown(
    """
    <style>
    /* Sidebar non redimensionnable horizontalement UNIQUEMENT quand elle est visible */
    section[data-testid="stSidebar"][aria-expanded="true"] {
        min-width: 350px;
        max-width: 350px;
        width: 350px;
        resize: none !important;
    }
    /* Boutons custom */
    .custom-btn-row {
        display: flex;
        gap: 10px;
        justify-content: space-between;
        margin-bottom: 10px;
    }
    .custom-btn-row .stButton > button,
    .custom-btn-row .stDownloadButton > button {
        min-width: 140px !important;
        max-width: 140px !important;
        width: 140px !important;
        white-space: nowrap;
        font-weight: 600;
        border-radius: 6px;
        padding: 0.5em 0.7em;
        font-size: 0.80em;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.set_page_config(page_title="🔎 Recherche Job / Alternance", layout="wide")
st.title("🔎 Recherche Job / Alternance")

init_db()

# Chargement/sauvegarde config utilisateur
if "config" not in st.session_state:
    st.session_state.config = DEFAULT_CONFIG.copy()

def save_config():
    with open("user_config.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.config, f, ensure_ascii=False, indent=2)

def load_config():
    try:
        with open("user_config.json", "r", encoding="utf-8") as f:
            st.session_state.config = json.load(f)
    except:
        st.warning("Aucun fichier de configuration trouvé.")

def export_config():
    st.download_button("Exporter config", data=json.dumps(st.session_state.config, ensure_ascii=False, indent=2), file_name="config_jobspy.json")

def import_config():
    uploaded = st.file_uploader("Importer config", type=["json"])
    if uploaded:
        st.session_state.config = json.load(uploaded)
        st.success("Configuration importée !")

def reset_config():
    st.session_state.config = DEFAULT_CONFIG.copy()
    st.success("Configuration réinitialisée.")

with st.sidebar:
    st.header("Paramètres de recherche")
    # Suppression des champs itinéraire dans la sidebar
    st.text_area("Mots-clés (un par ligne)", key="keywords", value="\n".join(st.session_state.config.get("keywords", [])), on_change=lambda: st.session_state.config.update({"keywords": st.session_state.keywords.splitlines()}))
    st.text_input("Localisation", key="location", value=st.session_state.config.get("location", ""), on_change=lambda: st.session_state.config.update({"location": st.session_state.location}))
    st.selectbox("Pays", options=[c.name for c in Country], key="country", index=list(Country).index(Country[st.session_state.config.get("country", "FRANCE")]), on_change=lambda: st.session_state.config.update({"country": st.session_state.country}))
    st.number_input("Rayon (km)", min_value=1, max_value=100, value=st.session_state.config.get("distance", 30), key="distance", on_change=lambda: st.session_state.config.update({"distance": st.session_state.distance}))
    st.number_input("Résultats/clé", min_value=1, max_value=50, value=st.session_state.config.get("results_per_keyword", 20), key="results_per_keyword", on_change=lambda: st.session_state.config.update({"results_per_keyword": st.session_state.results_per_keyword}))
    st.number_input("Offres publiées depuis (jours)", min_value=1, max_value=30, value=st.session_state.config.get("days_old", 7), key="days_old", on_change=lambda: st.session_state.config.update({"days_old": st.session_state.days_old}))
    st.markdown("---")
    # Boutons horizontaux stylés
    st.markdown('<div class="custom-btn-row">', unsafe_allow_html=True)
    colA, colB, colC = st.columns([1,1,1])
    save_clicked = export_clicked = reset_clicked = False
    with colA:
        save_clicked = st.button("Sauvegarder")
    with colB:
        export_clicked = st.download_button("Exporter", data=json.dumps(st.session_state.config, ensure_ascii=False, indent=2), file_name="config_jobspy.json", help="Exporter la configuration JSON")
    with colC:
        reset_clicked = st.button("Réinitialiser")
    st.markdown('</div>', unsafe_allow_html=True)
    # Affichage des messages de succès/alerte sous les boutons, sur toute la largeur
    if save_clicked:
        save_config()
        st.success("Paramètres sauvegardés !")
    if reset_clicked:
        reset_config()
    # Import config en-dessous, centré
    st.markdown("")
    st.markdown("<div style='text-align:center; margin-top: 10px; margin-bottom: 10px;'><b>Importer une config JSON</b></div>", unsafe_allow_html=True)
    import_config()
    st.markdown("---")
    if st.button("🔄 Scraper de nouvelles offres"):
        with st.spinner("Scraping en cours..."):
            jobs = scrape_all(
                st.session_state.config.get("keywords", []),
                st.session_state.config.get("location", ""),
                st.session_state.config.get("country", "FRANCE"),
                st.session_state.config.get("distance", 30),
                st.session_state.config.get("results_per_keyword", 20),
                st.session_state.config.get("days_old", 7) * 24,  # conversion jours -> heures
            )
            n = insert_jobs(jobs)
        if n > 0:
            st.success(f"{n} nouvelles offres ajoutées !")
        else:
            st.info("Aucune nouvelle offre trouvée.")

st.markdown("---")

# Filtres avancés
df = get_jobs_df()

# Statut
status_options = ["non candidaté", "candidature envoyée", "refusé", "accepté"]
col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
with col1:
    status_filter = st.selectbox("Filtre : Statut", options=["Tous"] + status_options)
with col2:
    entreprise_filter = st.selectbox("Entreprise", options=["Toutes"] + sorted(df["company"].dropna().unique().tolist()))
with col3:
    ville_filter = st.selectbox("Ville", options=["Toutes"] + sorted(set([v.split(",")[0] for v in df["location"].dropna() if v])))
with col4:
    source_filter = st.selectbox("Source", options=["Toutes"] + sorted(df["source"].dropna().unique().tolist()))
with col5:
    date_filter = st.selectbox("Date", options=["Toutes", "Aujourd'hui", "3 derniers jours", "7 derniers jours", "30 derniers jours"])
with col6:
    type_filter = st.text_input("Type de poste (mot-clé)")
with col7:
    motcle_filter = st.text_input("Mot-clé (titre/desc)")
with col8:
    non_candide_filter = st.checkbox("Non candidaté seulement")

# Application des filtres
if status_filter != "Tous":
    df = df[df["status"] == status_filter]
if entreprise_filter != "Toutes":
    df = df[df["company"] == entreprise_filter]
if ville_filter != "Toutes":
    df = df[df["location"].str.startswith(ville_filter)]
if source_filter != "Toutes":
    df = df[df["source"] == source_filter]
if date_filter != "Toutes":
    now = datetime.now()
    if date_filter == "Aujourd'hui":
        df = df[df["date_posted"] == now.strftime("%Y-%m-%d")]
    elif date_filter == "3 derniers jours":
        df = df[pd.to_datetime(df["date_posted"]) >= (now - pd.Timedelta(days=3))]
    elif date_filter == "7 derniers jours":
        df = df[pd.to_datetime(df["date_posted"]) >= (now - pd.Timedelta(days=7))]
    elif date_filter == "30 derniers jours":
        df = df[pd.to_datetime(df["date_posted"]) >= (now - pd.Timedelta(days=30))]
if type_filter:
    df = df[df["title"].str.contains(type_filter, case=False, na=False) | df["description"].str.contains(type_filter, case=False, na=False)]
if motcle_filter:
    df = df[df["title"].str.contains(motcle_filter, case=False, na=False) | df["description"].str.contains(motcle_filter, case=False, na=False)]
if non_candide_filter:
    df = df[df["status"] == "non candidaté"]

# Affichage tableau
st.subheader(f"{len(df)} offres en base")
if len(df) == 0:
    st.info("Aucune offre en base. Lancez un scraping !")
else:
    for i, row in df.iterrows():
        with st.expander(f"{row['title']} | {row['company']} | {row['location']} | {row['date_posted']}"):
            st.markdown(f"**Entreprise :** {row['company']}  ")
            st.markdown(f"**Localisation :** {row['location']}  ")
            st.markdown(f"**Date :** {row['date_posted']}  ")
            st.markdown(f"**Source :** {row['source']}")
            st.markdown(f"**Statut :** {row['status']}")
            st.markdown(f"**Description :**\n{row['description'][:1000]}...")
            # Recherche adresse complète si besoin (mais plus de calcul d'itinéraire)
            adresse_utilisee = None
            if hasattr(row, 'company_addresses') and row.get('company_addresses'):
                adresse_utilisee = row['company_addresses']
            else:
                company = row['company']
                city = row['location'].split(",")[0] if row['location'] else None
                adresse_utilisee = get_company_full_address(company, city, None)
            if adresse_utilisee:
                st.markdown(f"**Adresse trouvée (OpenStreetMap) :** {adresse_utilisee}")
            else:
                st.markdown("**Adresse trouvée (OpenStreetMap) :** Non trouvée")
            # Suppression du calcul et affichage d'itinéraire
            cols = st.columns([2,1,1,1])
            with cols[0]:
                if st.button("🌐 Ouvrir l'offre", key=f"open_{row['id']}"):
                    webbrowser.open_new_tab(row['url'])
            with cols[1]:
                new_status = st.selectbox("Changer statut", status_options, index=status_options.index(row['status']), key=f"status_{row['id']}")
                if new_status != row['status']:
                    update_status(row['id'], new_status)
                    st.experimental_rerun()
            with cols[2]:
                st.write("")
            with cols[3]:
                st.write("")

st.caption("Fait avec ❤️ et JobSpy | Streamlit | SQLite | OpenRouteService | by GPT-4") 