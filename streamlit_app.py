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

# --- 3. NAČÍTANIE DÁT (Zákazníci z Google Sheets) ---
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
    except Exception as e:
        st.error(f"Nepodarilo sa načítať databázu: {e}")
        return pd.DataFrame(columns=['zakaznik', 'krajina', 'lojalita'])

df_zakaznici = load_customers(sheet_zakaznici_url)

# Príprava zoznamu pre výber
seznam_zakaznikov = list(sorted(df_zakaznici['zakaznik'].unique()))
if "Nový zákazník (zadať ručne)" not in seznam_zakaznikov:
    seznam_zakaznikov.append("Nový zákazník (zadať ručne)")

# --- 4. HLAVNÝ RIADOK (Dátum | Označenie CP | Zákazník + Detaily) ---
# Rozdelíme na 3 hlavné sekcie, pričom tretia (Zákazník) bude najširšia
c1, c2, c3 = st.columns([1, 1.2, 4.5])

with c1:
    datum_ponuky = st.date_input("Dátum")

with c2:
    oznacenie_ponuky = st.text_input("Označenie CP", placeholder="napr. CP-2024-001")

with c3:
    # Ak je vybraný Nový zákazník, riadok sa vnútorne prekreslí na 5 stĺpcov
    if st.session_state.get("vybrany_zakaznik") == "Nový zákazník (zadať ručne)":
        sub1, sub2, sub3, sub4, sub5 = st.columns([1.5, 1.5, 0.8, 0.8, 0.8])
        
        with sub1:
            zakaznik_vyber = st.selectbox("Zákazník", options=seznam_zakaznikov, key="vybrany_zakaznik")
        with sub2:
            novy_zak_meno = st.text_input("Meno nového")
        with sub3:
            novy_zak_krajina = st.text_input("Krajina")
        with sub4:
            st.text_input("Lojalita", value="0.5", disabled=True)
        with sub5:
            st.write(" ") # Zarovnanie tlačidla
            if st.button("Uložiť"):
                if novy_zak_meno and novy_zak_krajina:
                    payload = {"zakaznik": novy_zak_meno, "krajina": novy_zak_krajina, "lojalita": 0.5}
                    api_url = "https://script.google.com/macros/s/AKfycbwNR33wxSNXJFo9-o2otM-mdKQE22s3i3y5n08dY7eogGhhKDTasiPn3zaOoSihppTq/exec"
                    try:
                        requests.post(api_url, json=payload)
                        st.session_state["vybrany_zakaznik"] = novy_zak_meno
                        st.success("OK")
                        st.rerun()
                    except:
                        st.error("Chyba API")
                else:
                    st.warning("Doplňte údaje")
                    
        # Premenné pre ďalšie výpočty (v prípade nového zákazníka)
        zakaznik, krajina, lojalita = novy_zak_meno, novy_zak_krajina, 0.5

    else:
        # Ak je vybraný existujúci zákazník, riadok má 3 stĺpce (Výber | Krajina | Lojalita)
        sub1, sub2, sub3 = st.columns([2, 1, 1])
        
        with sub1:
            zakaznik_vyber = st.selectbox("Zákazník", options=seznam_zakaznikov, key="vybrany_zakaznik")
        
        # Načítanie existujúcich hodnôt
        zakaznik = zakaznik_vyber
        data_zakaznika = df_zakaznici[df_zakaznici['zakaznik'] == zakaznik]
        
        if not data_zakaznika.empty:
            krajina = str(data_zakaznika['krajina'].values[0])
            raw_lojalita = str(data_zakaznika['lojalita'].values[0])
            # Čistenie lojality (premena na číslo)
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

# --- 5. PRIESTOR PRE ĎALŠIE VÝPOČTY ---
# Tu budeme pokračovať s pridávaním položiek...

