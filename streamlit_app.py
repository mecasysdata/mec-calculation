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

# --- 5. RIADOK: POLOŽKA (ITEM) ---
# Vytvoríme nový riadok stĺpcov

col5, col6, col7, col8,col9, col10, col11, col12 = st.columns(8)
 
with col5:
    # Atribút: item
    # UX zobrazenie: ITEM
    # Dátový typ: string (st.text_input automaticky vracia string)
    item = st.text_input("ITEM", key="item_input")

with col6:
    # Atribút: pocet_kusov 
    # Vždy celé číslo (value=1), minimálne 1 (min_value=1)
    pocet_kusov = st.number_input(
        "Počet kusov", 
        min_value=1, 
        value=1, 
        step=1, 
        key="pocet_input",
        help="Zadajte celkové množstvo kusov (minimálne 1)."
    )

with col7:
    # Atribút: narocnost
    # UX zobrazenie: Náročnosť
    # Výber z možností 1 až 5
    narocnost = st.selectbox(
        "Náročnosť", 
        options=[1, 2, 3, 4, 5], 
        index=0,  # Predvolene vybratá prvá možnosť (1)
        key="narocnost_input",
        help="Vyberte stupeň náročnosti od 1 (najnižšia) po 5 (najvyššia)."
    )

with col8:
    # Atribút: tvar
    # UX zobrazenie: Tvar
    # Výber z možností: STV (Štvorec/Obdĺžnik) alebo KR (Kruh)
    tvar = st.selectbox(
        "Tvar", 
        options=["STV", "KR"], 
        key="tvar_input",
        help="STV = štvorcový alebo obdĺžnikový tvar, KR = kruhový tvar"
    )

# --- DOPLNENÉ ROZMERY PODĽA TVARU ---

if tvar == "KR":
    with col9:
        d = st.number_input("D(mm)", min_value=0.0, step=0.1, format="%.1f", key="d_kr")
    with col10:
        l = st.number_input("L(mm)", min_value=0.0, step=0.1, format="%.1f", key="l_kr")
    # Inicializácia ostatných premenných pre model
    s, v = 0.0, 0.0
else:
    with col9:
        d = st.number_input("D/P(mm)", min_value=0.0, step=0.1, format="%.1f", key="d_stv")
    with col10:
        s = st.number_input("S(mm)", min_value=0.0, step=0.1, format="%.1f", key="s_stv")
    with col11:
        v = st.number_input("V(mm)", min_value=0.0, step=0.1, format="%.1f", key="v_stv")
    # Inicializácia ostatných premenných pre model
    l = 0.0
