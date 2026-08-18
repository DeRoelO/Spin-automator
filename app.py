import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import spin_core
import os
import json
import subprocess
import sys
import time
import signal

st.set_page_config(page_title="SPIN Aanvrager", layout="wide")

SETTINGS_FILE = "user_settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

saved = load_settings()

def get_val(key, default):
    return saved.get(key, default)

def get_time(key, default_str):
    t_str = saved.get(key, default_str)
    try:
        return datetime.strptime(t_str, "%H:%M").time()
    except:
        return datetime.strptime(default_str, "%H:%M").time()

st.title("🚧 SPIN Automator")
st.markdown("Vul hieronder je gegevens in, stel je routes en dagen in, en genereer automatisch de SPIN meldingen.")

DISTRICTS = [
    "ON District Zuid", "ON District Noord", "ON District Oost",
    "MN District Noord", "MN District Zuid",
    "NN District West", "NN District Oost",
    "WNN District Noord", "WNN District Zuid",
    "WNZ District Noord", "WNZ District Zuid",
    "ZN District West", "ZN District Midden", "ZN District Oost",
    "Zee en Delta Noord", "Zee en Delta Zuid"
]

STD_OPMERKING = (
    "Betreft inspectiewerkzaamheden voor MJPV in opdracht van RWS. Inspectie dient gedaan te worden bij daglicht "
    "De inspecties worden gedaan vanaf de vluchtstrook waar de  vluchtstrook aanwezig is. Waar geen vluchtstrook "
    "aanwezig is, wordt met het verkeer mee gereden.De inspectie is weersathankelijk, mag niet gedaan worden bij "
    "een nat wegdek en niet bij helder weer. Vanwege deze onzekerheid worden meeredere dagen ingepland."
)

with st.sidebar:
    st.header("1. Inloggegevens")
    username = st.text_input("SPIN Gebruikersnaam", value=get_val("username", os.environ.get("SPIN_USER", "")))
    password = st.text_input("SPIN Wachtwoord", type="password", value=get_val("password", os.environ.get("SPIN_PASS", "")))
    
    st.header("2. Persoonsgegevens")
    achternaam = st.text_input("Achternaam", value=get_val("achternaam", ""))
    tussenvoegsel = st.text_input("Tussenvoegsel", value=get_val("tussenvoegsel", ""))
    voornaam = st.text_input("Voornaam", value=get_val("voornaam", ""))
    
    st.markdown("*Deze gegevens worden gebruikt voor de velden 'Contactpersoon' en 'Contactpersoon Uitvoering'.*")
    
    st.header("Instellingen")
    headless = st.checkbox("Headless Modus (Onzichtbare Browser)", value=get_val("headless", True), help="Zet dit UIT als je live mee wilt kijken.")
    auto_split = st.checkbox("Lange routes auto-splitsen (20km)", value=get_val("auto_split", True), help="Vink uit om in één keer een groot vak (>20km) aan te vragen.")

    st.markdown("---")
    st.markdown("### Geavanceerd")
    if st.button("🛑 Noodstop (Afbreken)", use_container_width=True):
        try:
            if os.path.exists("pid.txt"):
                with open("pid.txt", "r") as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                st.success("✅ Proces succesvol afgebroken!")
        except:
            st.info("Geen actief proces gevonden.")

st.header("3. Algemene Aanvraag Gegevens")
col1, col2 = st.columns(2)
with col1:
    besteknummer = st.text_input("Besteksnummer", value=get_val("besteknummer", "NL-31154600"))
    
    def_district = get_val("district", "ON District Zuid")
    d_index = DISTRICTS.index(def_district) if def_district in DISTRICTS else 0
    district = st.selectbox("District (Wegbeheerder & Verkeersloket)", DISTRICTS, index=d_index)
    
with col2:
    opmerking = st.text_area("Opmerking", value=get_val("opmerking", STD_OPMERKING), height=130)

st.header("4. Dagen & Tijden")

def get_12th_working_day(start_date):
    days_added = 0
    current_date = start_date
    while days_added < 12:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:  
            days_added += 1
    return current_date

min_allowed_date = get_12th_working_day(date.today())
st.warning(f"⚠️ **SPIN-regel**: Aanvragen binnen 12 werkdagen (vóór **{min_allowed_date.strftime('%d-%m-%Y')}**) zijn officieel niet toegestaan, tenzij bij uitzondering.")

if "selected_dates" not in st.session_state:
    st.session_state.selected_dates = []

c1, c2 = st.columns([2, 1])
with c1:
    new_date = st.date_input("Kies een specifieke datum", format="DD.MM.YYYY")
with c2:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    if st.button("➕ Voeg datum toe", use_container_width=True):
        if new_date not in st.session_state.selected_dates:
            st.session_state.selected_dates.append(new_date)
            st.session_state.selected_dates.sort()
            st.rerun()

if st.session_state.selected_dates:
    DAYS_NL = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
    st.session_state.selected_dates = st.multiselect(
        "Geselecteerde datums (klik op een kruisje om te verwijderen):",
        options=st.session_state.selected_dates,
        default=st.session_state.selected_dates,
        format_func=lambda d: f"{DAYS_NL[d.weekday()]} {d.strftime('%d.%m.%Y')}" + (" ⚠️ (Binnen 12 wkd)" if d < min_allowed_date else "")
    )
else:
    st.info("Nog geen datums toegevoegd. Gebruik de knop hierboven.")

dates = st.session_state.selected_dates

t_col1, t_col2 = st.columns(2)
with t_col1:
    st.subheader("Werkweek (Ma-Vr)")
    start_week = st.time_input("Starttijd", value=get_time("start_week", "09:00"))
    end_week = st.time_input("Eindtijd", value=get_time("end_week", "15:00"))
with t_col2:
    st.subheader("Weekend (Za-Zo)")
    start_weekend = st.time_input("Starttijd Weekend", value=get_time("start_weekend", "08:00"))
    end_weekend = st.time_input("Eindtijd Weekend", value=get_time("end_weekend", "16:00"))

st.header("5. Routes (Onbeperkt)")
if "route_data" not in st.session_state:
    st.session_state.route_data = pd.DataFrame([
        {"Wegnummer": "A15", "Wegzijde": "Re", "Van km": 150.0, "Tot km": 200.0}
    ])

edited_routes = st.data_editor(st.session_state.route_data, num_rows="dynamic", use_container_width=True)

if st.button("Genereer Samenvatting & Plan Meldingen", type="primary"):
    if not dates:
        st.error("Selecteer minimaal één datum!")
    elif edited_routes.empty:
        st.error("Voeg minimaal één route toe!")
    else:
        tasks = []
        for d in dates:
            is_weekend = d.weekday() >= 5
            t_start = start_weekend if is_weekend else start_week
            t_end = end_weekend if is_weekend else end_week
            
            start_str = f"{d.strftime('%d.%m.%Y')}, {t_start.strftime('%H:%M')}"
            end_str = f"{d.strftime('%d.%m.%Y')}, {t_end.strftime('%H:%M')}"

            for _, row in edited_routes.iterrows():
                if pd.isna(row['Wegnummer']) or pd.isna(row['Van km']) or pd.isna(row['Tot km']):
                    continue
                
                f_km = float(row['Van km'])
                t_km = float(row['Tot km'])
                
                if auto_split:
                    segments = spin_core.calculate_measure_segments(f_km, t_km)
                else:
                    segments = [(f_km, t_km)]
                    
                for s_from, s_to in segments:
                    tasks.append({
                        "Datum": d.strftime("%d.%m.%Y"),
                        "Start": start_str,
                        "End": end_str,
                        "Wegnummer": str(row['Wegnummer']),
                        "Wegzijde": str(row['Wegzijde']),
                        "Van km": spin_core.format_km(s_from),
                        "Tot km": spin_core.format_km(s_to)
                    })
        
        st.session_state.tasks = tasks

if "tasks" in st.session_state and st.session_state.tasks:
    st.subheader(f"Geplande Meldingen ({len(st.session_state.tasks)} totaal)")
    st.dataframe(pd.DataFrame(st.session_state.tasks), use_container_width=True)
    
    st.markdown("### 📋 Controle en Bevestiging")
    st.info(f"Op basis van de ingevoerde gegevens worden er in totaal **{len(st.session_state.tasks)}** conceptmeldingen in SPIN geplaatst. Controleer het bovenstaande overzicht zorgvuldig.")
    
    if st.button("✅ Gegevens akkoord, start automatisering", type="primary"):
        
        save_settings({
            "username": username,
            "password": password,
            "achternaam": achternaam,
            "tussenvoegsel": tussenvoegsel,
            "voornaam": voornaam,
            "headless": headless,
            "auto_split": auto_split,
            "besteknummer": besteknummer,
            "district": district,
            "opmerking": opmerking,
            "start_week": start_week.strftime("%H:%M"),
            "end_week": end_week.strftime("%H:%M"),
            "start_weekend": start_weekend.strftime("%H:%M"),
            "end_weekend": end_weekend.strftime("%H:%M")
        })

        tv = tussenvoegsel.strip() + " " if tussenvoegsel.strip() else ""
        naam_dropdown = f"{tv}{achternaam.strip()}, {voornaam.strip()}"
        naam_potlood = f"{achternaam.strip()} {tussenvoegsel.strip()}".strip()
        
        config = {
            "username": username,
            "password": password,
            "naam_dropdown": naam_dropdown,
            "naam_potlood": naam_potlood,
            "besteknummer": besteknummer,
            "district": district,
            "opmerking": opmerking,
            "headless": headless
        }
        
        job_data = {"tasks": st.session_state.tasks, "config": config}
        with open("job.json", "w", encoding="utf-8") as f:
            json.dump(job_data, f)
            
        with open("run.log", "w", encoding="utf-8") as f:
            f.write("🚀 Initialiseren van onafhankelijk achtergrondproces...\n")
            
        st.markdown("---")
        st.subheader("Terminal / Logging")
        log_container = st.empty()
        
        proc = subprocess.Popen([sys.executable, "spin_runner.py"])
        with open("pid.txt", "w") as f:
            f.write(str(proc.pid))
        
        try:
            while proc.poll() is None:
                try:
                    with open("run.log", "r", encoding="utf-8") as f:
                        log_text = f.read()
                    log_container.code(log_text, language="shell")
                except:
                    pass
                time.sleep(1)
        except BaseException:
            # Vangt op als Streamlit geforceerd herlaadt (bijv door een knop in te drukken)
            try: proc.kill() 
            except: pass
            raise
            
        try:
            with open("run.log", "r", encoding="utf-8") as f:
                log_text = f.read()
            log_container.code(log_text, language="shell")
        except:
            pass
            
        st.success("✅ Automatisering is afgerond!")
