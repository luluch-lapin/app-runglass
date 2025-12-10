import streamlit as st
import fitparse
import matplotlib.pyplot as plt
import io
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="RunGlass - Design Studio", page_icon="🎨", layout="wide")
st.title("🏆 RunGlass - Design Studio")

# --- FONCTIONS TECHNIQUES ---
def semi_circles_to_degrees(semicircles):
    if semicircles is None: return None
    return semicircles * (180 / 2**31)

def calculer_allure(distance_km, temps_sec):
    if distance_km <= 0 or temps_sec <= 0: return "0:00 min/km"
    temps_min = temps_sec / 60
    allure_decimal = temps_min / distance_km
    minutes = int(allure_decimal)
    secondes = int((allure_decimal - minutes) * 60)
    return f"{minutes}:{secondes:02d} min/km"

def formater_temps(secondes):
    m, s = divmod(int(secondes), 60)
    h, m = divmod(m, 60)
    if h > 0: return f"{h}h {m}min"
    return f"{m}min {s}s"

def lire_fit(file):
    fitfile = fitparse.FitFile(file)
    lats, lons = [], []
    dist_totale = 0
    temps_total = 0
    date_course = None
    
    for record in fitfile.get_messages("record"):
        lat = record.get_value("position_lat")
        lon = record.get_value("position_long")
        if lat and lon:
            lats.append(semi_circles_to_degrees(lat))
            lons.append(semi_circles_to_degrees(lon))

    for session in fitfile.get_messages("session"):
        if session.get_value("total_distance"): dist_totale = session.get_value("total_distance")
        if session.get_value("total_timer_time"): temps_total = session.get_value("total_timer_time")
        if session.get_value("start_time"): date_course = session.get_value("start_time")
        
    return lats, lons, dist_totale, temps_total, date_course

# --- INTERFACE ---
with st.sidebar:
    st.header("1. Fichier Source")
    uploaded_file = st.file_uploader("Fichier .FIT", type=['fit'])
    
    # Valeurs par défaut
    default_stats = "En attente..."
    default_date = "JJ/MM/AAAA"
    lats, lons = [], []
    
    if uploaded_file is not None:
        bytes_data = uploaded_file.read()
        lats, lons, dist_m, duree_s, date_obj = lire_fit(io.BytesIO(bytes_data))
        
        dist_km = dist_m / 1000
        stats_auto = f"{dist_km:.2f} km  |  {formater_temps(duree_s)}  |  {calculer_allure(dist_km, duree_s)}"
        default_stats = stats_auto
        if date_obj:
            default_date = date_obj.strftime("%d/%m/%Y") 
        uploaded_file.seek(0)

    st.header("2. Textes")
    titre_course = st.text_input("Titre", "COURSE OFFICIELLE")
    date_texte = st.text_input("Date", value=default_date)
    stats_course = st.text_input("Statistiques", value=default_stats)
    
    st.header("3. Design & Position")
    couleur_trace = st.color_picker("Couleur Tracé", "#fc4c02")
    couleur_texte = st.color_picker("Couleur Texte", "#000000")
    
    # NOUVEAU : Réglage fin de l'espacement
    st.subheader("Ajustements")
    # Position de base des stats (le plus bas)
    y_base = st.slider("Hauteur du bloc texte", 0.05, 0.20, 0.10)
    # Écart entre les lignes
    gap = st.slider("Écart entre les lignes", 0.02, 0.10, 0.04)

# --- GÉNÉRATION ---
def generer_visuel(lats, lons, titre, date, stats, col_trace, col_text, y_bottom, line_gap):
    if not lats: return None
    
    fig, ax = plt.subplots(figsize=(10, 14), facecolor='none')
    
    # Zoom
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    max_range = max(max_lat - min_lat, max_lon - min_lon)
    buffer = max_range * 0.6
    
    ax.set_xlim(center_lon - buffer, center_lon + buffer)
    ax.set_ylim(center_lat - buffer, center_lat + buffer)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_facecolor('none')

    # Tracé
    ax.plot(lons, lats, color=col_trace, linewidth=6, solid_capstyle='round')
    
    # --- BLOC TEXTE HARMONISÉ ---
    # On calcule les positions relatives les unes aux autres
    y_stats = y_bottom
    y_date = y_bottom + line_gap
    y_titre = y_bottom + (line_gap * 2.2) # Le titre est un peu plus haut
    
    # Police commune : sans-serif (plus propre)
    police = 'sans-serif'
    
    # 1. TITRE (Même police, pas de gras forcé, juste plus grand)
    plt.figtext(0.5, y_titre, titre.upper(), # .upper() force les majuscules c'est plus joli
                fontsize=30, 
                color=col_text, 
                ha='center', fontfamily=police)

    # 2. DATE
    plt.figtext(0.5, y_date, date, 
                fontsize=18, color=col_text, 
                ha='center', fontfamily=police)

    # 3. STATS
    plt.figtext(0.5, y_stats, stats, 
                fontsize=22, color=col_text, 
                ha='center', fontfamily=police)
    
    return fig

# Affichage
if uploaded_file and lats:
    fig = generer_visuel(lats, lons, titre_course, date_texte, stats_course, couleur_trace, couleur_texte, y_base, gap)
    st.pyplot(fig, transparent=True)
    
    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format='png', dpi=300, transparent=True, bbox_inches=None, facecolor='none')
    img_buffer.seek(0)
    st.download_button("⬇️ TÉLÉCHARGER PNG", data=img_buffer, file_name="trophee_design.png", mime="image/png")

else:
    st.info("👈 Importez un fichier .FIT pour commencer.")