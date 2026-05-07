import streamlit as st
import pandas as pd
import requests
import datetime

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
col1, col2, col3, col4 = st.columns(4)

with col1:
    datum = st.date_input("Dátum", datetime.date.today())

with col2:
    ponuka = st.text_input("Označenie CP")

# --- LOGIKA PRE ZOZNAM ZÁKAZNÍKOV ---
moznosti_zakaznikov = ["+ Pridať nového zákazníka"] + zoznam_zakaznikov

with col3:
    vyber = st.selectbox("Názov Zákazníka", moznosti_zakaznikov)

# --- KONFIGURÁCIA UKLADANIA ---
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwNR33wxSNXJFo9-o2otM-mdKQE22s3i3y5n08dY7eogGhhKDTasiPn3zaOoSihppTq/exec"

# --- LOGIKA ROZHODOVANIA (Opravené poradie a odstránená duplicita) ---
if vyber == "+ Pridať nového zákazníka":
    with col3:
        zakaznik = st.text_input("Zadajte meno nového zákazníka", key="new_cust_name")
    
    with col4:
        # Najprv vytvoríme krajinu, aby ju tlačidlo neskôr poznalo
        krajina_hodnota = st.text_input("Krajina Zákazníka (manuálne)", key="new_cust_country")
        lojalita = 0.5

    with col3:
        # Tlačidlo je až TU, aby videlo premennú 'krajina_hodnota' z riadku vyššie
        st.markdown(" ") 
        if st.button("💾 Uložiť do databázy", use_container_width=True, type="primary"):
            if zakaznik.strip() and krajina_hodnota.strip():
                novy_zakaznik_data = {"zakaznik": zakaznik, "krajina": krajina_hodnota}
                try:
                    response = requests.post(WEB_APP_URL, json=novy_zakaznik_data)
                    if response.status_code == 200:
                        st.success(f"Zákazník '{zakaznik}' uložený!")
                        st.balloons()
                        st.cache_data.clear()
                    else:
                        st.error("Chyba pri ukladaní!")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("⚠️ Vyplňte meno aj krajinu!")

else:
    # REŽIM: EXISTUJÚCI ZÁKAZNÍK
    data_zakaznika = df[df['zakaznik'] == vyber].iloc[0]
    zakaznik = vyber
    krajina_hodnota = str(data_zakaznika['krajina'])
    lojalita = float(data_zakaznika['lojalita'])
    
    with col4:
        st.text_input("Krajina Zákazníka", value=krajina_hodnota, disabled=True)
st.divider()
