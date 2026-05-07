import streamlit as st
import pandas as pd
import requests
import re

# --- 1. NASTAVENIA ---
st.set_page_config(layout="wide", page_title="MEC Calculation")

# --- 2. LOGO A NÁZOV ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    try: st.image("logo.png", width=150)
    except: st.write("🖼️ Logo")
with col_title:
    st.title("MEC Calculation")

st.divider()

# Načítanie dát z Google Sheet - zákazník
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSuHQWbpryWNerWr8aKKheHbzTPhXI6lS7YH1sL5zwFIIzLfpTZz47acY_ua2e_fVqEcfxMBe5wnjue/pub?gid=0&single=true&output=csv"
df = pd.read_csv(sheet_url)

# Príprava zoznamu zákazníkov (zoradený abecedne)
zoznam_zakaznikov = sorted(df['zakaznik'].unique())
# --- 3. RIADOK S ATRIBÚTMI ---
# Vytvoríme si stĺpce, aby sme mohli dávať prvky vedľa seba
col1, col2, col3, col4 = st.columns(4)

with col1:
    # Atribút Dátum: 
    # - label: "Dátum" (názov políčka)
    # - value: defaultne nastavený na dnešok (datetime.date.today())
    import datetime
    datum = st.date_input("Dátum", datetime.date.today())

with col2:
    # Atribút Ponuka:
    # - label: "Označenie CP" (názov, ktorý uvidí používateľ)
    # - value: "" (necháme prázdne, aby používateľ mohol písať)
    ponuka = st.text_input("Označenie CP")
# --- LOGIKA PRE ZOZNAM ZÁKAZNÍKOV ---
# Pridáme možnosť pre nového zákazníka na začiatok zoznamu
moznosti_zakaznikov = ["+ Pridať nového zákazníka"] + zoznam_zakaznikov

with col3:
    vyber = st.selectbox("Názov Zákazníka", moznosti_zakaznikov)

# --- LOGIKA ROZHODOVANIA ---
if vyber == "+ Pridať nového zákazníka":
    # Režim: Nový zákazník
    with col3:
        zakaznik = st.text_input("Zadajte meno nového zákazníka")
    
    with col4:
        krajina_hodnota = st.text_input("Krajina Zákazníka (manuálne)")
    
    lojalita = 0.5  # Automaticky nastavená hodnota

else:
    # Režim: Existujúci zákazník (pôvodná logika)
    data_zakaznika = df[df['zakaznik'] == vyber].iloc[0]
    zakaznik = vyber
    krajina_hodnota = str(data_zakaznika['krajina'])
    lojalita = float(data_zakaznika['lojalita'])

    with col4:
        # Pole zostáva uzamknuté (disabled), keďže krajinu poznáme
        st.text_input("Krajina Zákazníka", value=krajina_hodnota, disabled=True)
