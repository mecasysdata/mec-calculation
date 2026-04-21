import streamlit as st
import streamlit as st
import pandas as pd
import requests
import re

# --- KONFIGURÁCIA STRÁNKY ---
st.set_page_config(layout="wide") # Roztiahne aplikáciu na celú šírku, aby stĺpce nevyzerali stiesnene

# --- HLAVIČKA (Logo a Názov) ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image("logo.png", width=150)
with col_title:
    st.title("MEC Calculation")
    st.write("Vitajte vo vašej aplikácii na výpočet cien!")

st.divider()

# --- NAČÍTANIE DÁT ---
sheet_zakaznici_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSuHQWbpryWNerWr8aKKheHbzTPhXI6lS7YH1sL5zwFIIzLfpTZz47acY_ua2e_fVqEcfxMBe5wnjue/pub?gid=0&single=true&output=csv"

@st.cache_data
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
seznam_zakaznikov = list(sorted(df_zakaznici['zakaznik'].unique()))
if "Nový zákazník (zadať ručne)" not in seznam_zakaznikov:
    seznam_zakaznikov.append("Nový zákazník (zadať ručne)")

# --- HLAVNÝ RIADOK (Dátum | Označenie | Výber zákazníka) ---
c1, c2, c3 = st.columns([1, 1.5, 2])

with c1:
    datum_ponuky = st.date_input("Dátum")

with c2:
    oznacenie_ponuky = st.text_input("Označenie CP", placeholder="napr. CP-2024-001")

with c3:
    zakaznik_vyber = st.selectbox("Vyberte zákazníka", options=seznam_zakaznikov, key="vybrany_zakaznik")

# --- LOGIKA A ZOBRAZENIE INFO O ZÁKAZNÍKOVI ---
zakaznik, krajina, lojalita = "", "", 0.5

if zakaznik_vyber == "Nový zákazník (zadať ručne)":
    col_n1, col_n2, col_n3 = st.columns([2, 2, 1])
    with col_n1:
        zakaznik = st.text_input("Meno nového zákazníka")
    with col_n2:
        krajina = st.text_input("Krajina")
    with col_n3:
        st.write(" ") # Odstup
        if st.button("🚀 Uložiť"):
            if zakaznik and krajina:
                payload = {"zakaznik": zakaznik, "krajina": krajina, "lojalita": 0.5}
                api_url = "https://script.google.com/macros/s/AKfycbwNR33wxSNXJFo9-o2otM-mdKQE22s3i3y5n08dY7eogGhhKDTasiPn3zaOoSihppTq/exec"
                requests.post(api_url, json=payload)
                st.success("Uložené!")
                st.rerun()
else:
    zakaznik = zakaznik_vyber
    data_zakaznika = df_zakaznici[df_zakaznici['zakaznik'] == zakaznik]
    if not data_zakaznika.empty:
        krajina = str(data_zakaznika['krajina'].values[0])
        raw_lojalita = str(data_zakaznika['lojalita'].values[0])
        clean_lojalita = re.sub(r'[^0-9.]', '', raw_lojalita.replace(',', '.'))
        try:
            lojalita = float(clean_lojalita)
        except:
            lojalita = 0.5

# Zobrazenie detailov zákazníka hneď pod výberom
if zakaznik_vyber != "Nový zákazník (zadať ručne)":
    st.info(f"🌍 **Krajina:** {krajina} | ⭐ **Lojalita:** {lojalita}")
