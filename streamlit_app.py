import streamlit as st
import streamlit as st
import pandas as pd
import requests
import re

# Vytvoríme dva stĺpce: prvý pre logo (šírka 1) a druhý pre text (šírka 3)
# Pomer 1:3 zabezpečí, že logo nebude príliš dominantné
col1, col2 = st.columns([1, 3])

with col1:
    st.image("logo.png")

with col2:
    st.title("MEC Calculation")
    st.write("Vitajte vo vašej aplikácii na výpočet cien!")

st.divider() # Pridá jemnú deliacu čiaru

#zaciatok aplikacie
# Vytvoríme dva stĺpce pre Dátum a Označenie
col_date, col_ref = st.columns([1, 1])

with col_date:
    # Atribút Dátum - predvolene nastavený na dnešok
    datum_ponuky = st.date_input("Dátum", help="Zadajte dátum vytvorenia ponuky")

with col_ref:
    # Atribút Označenie cenovej ponuky - voľný textový vstup
    oznacenie_ponuky = st.text_input("Označenie cenovej ponuky", placeholder="napr. CP-2024-001")

# --- 3. NAČÍTANIE DÁT (Vaša logika) ---
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
    except Exception:
        # Záložný prázdny DataFrame, ak by sheet nefungoval
        return pd.DataFrame(columns=['zakaznik', 'krajina', 'lojalita'])

df_zakaznici = load_customers(sheet_zakaznici_url)

st.subheader("Informácie o zákazníkovi")

# Správa session_state pre nového zákazníka
if "novy_zakaznik_meno" in st.session_state:
    st.session_state["vybrany_zakaznik"] = st.session_state["novy_zakaznik_meno"]
    del st.session_state["novy_zakaznik_meno"]

# Príprava zoznamu zákazníkov
seznam_zakaznikov = list(sorted(df_zakaznici['zakaznik'].unique()))

if "vybrany_zakaznik" in st.session_state:
    meno_noveho = st.session_state["vybrany_zakaznik"]
    if meno_noveho not in seznam_zakaznikov:
        seznam_zakaznikov.append(meno_noveho)
        seznam_zakaznikov.sort()

if "Nový zákazník (zadať ručne)" not in seznam_zakaznikov:
    seznam_zakaznikov.append("Nový zákazník (zadať ručne)")

# --- 4. VÝBER ZÁKAZNÍKA ---
zakaznik_vyber = st.selectbox("Vyberte zákazníka", options=seznam_zakaznikov, key="vybrany_zakaznik")

# Inicializácia premenných
zakaznik = ""
krajina = ""
lojalita = 0.5

if zakaznik_vyber == "Nový zákazník (zadať ručne)":
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        zakaznik = st.text_input("Meno nového zákazníka:")
    with col_n2:
        krajina = st.text_input("Krajina zákazníka:")
    
    lojalita = 0.5

    if st.button("🚀 Uložiť zákazníka do databázy"):
        if zakaznik and krajina:
            payload = {"zakaznik": zakaznik, "krajina": krajina, "lojalita": lojalita}
            try:
                api_url = "https://script.google.com/macros/s/AKfycbwNR33wxSNXJFo9-o2otM-mdKQE22s3i3y5n08dY7eogGhhKDTasiPn3zaOoSihppTq/exec"
                requests.post(api_url, json=payload)
                st.session_state["novy_zakaznik_meno"] = zakaznik
                st.success(f"Zákazník **{zakaznik}** bol odoslaný!")
                st.rerun() # Refresh aby sa pridal do zoznamu
            except Exception as e:
                st.error(f"Chyba: {e}")
        else:
            st.warning("Vyplňte meno aj krajinu.")

    if not zakaznik or not krajina:
        st.stop()

else:
    zakaznik = zakaznik_vyber
    data_zakaznika = df_zakaznici[df_zakaznici['zakaznik'] == zakaznik]
    
    if not data_zakaznika.empty:
        krajina = str(data_zakaznika['krajina'].values[0])
        raw_lojalita = str(data_zakaznika['lojalita'].values[0])
        clean_lojalita = re.sub(r'[^0-9.]', '', raw_lojalita.replace(',', '.'))
        try:
            lojalita = float(clean_lojalita)
        except ValueError:
            lojalita = 0.5
    else:
        krajina = "Neznáma"
        lojalita = 0.5

# Zobrazenie výsledku (v prehľadnom boxe)
st.info(f"📍 **Zákazník:** {zakaznik} | 🌍 **Krajina:** {krajina} | ⭐ **Lojalita:** {lojalita}")
