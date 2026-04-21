import streamlit as st
import pandas as pd
import requests
import re

# --- 1. KONFIGURÁCIA STRÁNKY (Nutné pre široké zobrazenie) ---
st.set_page_config(layout="wide", page_title="MEC Calculation")

# --- 2. HLAVIČKA (Logo a Názov) ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    try:
        st.image("logo.png", width=150)
    except:
        st.write("🖼️ Logo")
with col_title:
    st.title("MEC Calculation")
    st.write("Vitajte vo vašej aplikácii na výpočet cien!")

st.divider()

# --- 3. NAČÍTANIE DÁT ---
sheet_zakaznici_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSuHQWbpryWNerWr8aKKheHbzTPhXI6lS7YH1sL5zwFIIzLfpTZz47acY_ua2e_fVqEcfxMBe5wnjue/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_customers(url):
    try:
        data = pd.read_csv(url)
        data.columns = data.columns.str.strip()
        for col in data.columns:
            if data[col].dtype == 'object':
                data[col] = data[col].astype(str).str.strip()
        return data
    except:
        return pd.DataFrame(columns=['zakaznik', 'krajina', 'lojalita'])

df_zakaznici = load_customers(sheet_zakaznici_url)

# Session State logika
if "novy_zakaznik_meno" in st.session_state:
    st.session_state["vybrany_zakaznik"] = st.session_state["novy_zakaznik_meno"]
    del st.session_state["novy_zakaznik_meno"]

seznam_zakaznikov = list(sorted(df_zakaznici['zakaznik'].unique()))
if "Nový zákazník (zadať ručne)" not in seznam_zakaznikov:
    seznam_zakaznikov.append("Nový zákazník (zadať ručne)")

# --- 4. EXTRÉMNE ŠIROKÝ RIADOK (Všetko v jednom) ---
# Definujeme stĺpce pre celý formulár
c1, c2, c3 = st.columns([1, 1.2, 6]) # c3 je veľký priestor pre zákazníka

with c1:
    datum_ponuky = st.date_input("Dátum")

with c2:
    oznacenie_ponuky = st.text_input("Označenie CP", placeholder="napr. CP-001")

with c3:
    # Vnútorné rozdelenie tretieho stĺpca podľa toho, čo vyberieme
    if st.session_state.get("vybrany_zakaznik") == "Nový zákazník (zadať ručne)":
        # Rozloženie pre NOVÉHO zákazníka (5 častí)
        sub1, sub2, sub3, sub4, sub5 = st.columns([1.5, 1.5, 1, 0.7, 0.8])
        with sub1:
            zakaznik_vyber = st.selectbox("Zákazník", options=seznam_zakaznikov, key="vybrany_zakaznik")
        with sub2:
            zakaznik = st.text_input("Meno", key="n_meno")
        with sub3:
            krajina = st.text_input("Krajina", key="n_kraj")
        with sub4:
            lojalita = 0.5
            st.text_input("Lojalita", value="0.5", disabled=True)
        with sub5:
            st.write(" ") # Zarovnanie na úroveň inputov
            if st.button("Uložiť"):
                if zakaznik and krajina:
                    api_url = "https://script.google.com/macros/s/AKfycbwNR33wxSNXJFo9-o2otM-mdKQE22s3i3y5n08dY7eogGhhKDTasiPn3zaOoSihppTq/exec"
                    try:
                        requests.post(api_url, json={"zakaznik": zakaznik, "krajina": krajina, "lojalita": 0.5}, timeout=10)
                        st.session_state["novy_zakaznik_meno"] = zakaznik
                        st.rerun()
                    except: st.error("API Chyba")
    else:
        # Rozloženie pre EXISTUJÚCEHO zákazníka (3 časti)
        sub1, sub2, sub3 = st.columns([2.5, 1.5, 1.5])
        with sub1:
            zakaznik_vyber = st.selectbox("Zákazník", options=seznam_zakaznikov, key="vybrany_zakaznik")
        
        zakaznik = zakaznik_vyber
        data_zakaznika = df_zakaznici[df_zakaznici['zakaznik'] == zakaznik]
        if not data_zakaznika.empty:
            krajina = str(data_zakaznika['krajina'].values[0])
            raw_lojalita = str(data_zakaznika['lojalita'].values[0])
            clean_lojalita = re.sub(r'[^0-9.]', '', raw_lojalita.replace(',', '.'))
            try: lojalita = float(clean_lojalita)
            except: lojalita = 0.5
        else:
            krajina, lojalita = "---", 0.5

        with sub2:
            st.text_input("Krajina", value=krajina, disabled=True)
        with sub3:
            st.text_input("Lojalita", value=lojalita, disabled=True)

st.divider()

# Validácia pre stop skriptu
if zakaznik_vyber == "Nový zákazník (zadať ručne)" and (not zakaznik or not krajina):
    st.info("Zadajte údaje nového zákazníka v riadku vyššie.")
    st.stop()

# --- Pokračovanie aplikácie ---
st.success(f"Pripravené pre: **{zakaznik}** | {krajina} | Lojalita: {lojalita}")
