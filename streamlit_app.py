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

# --- NAČÍTANIE DÁT (Zákazníci aj Materiály musia byť na začiatku) ---
# Zákazníci
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSuHQWbpryWNerWr8aKKheHbzTPhXI6lS7YH1sL5zwFIIzLfpTZz47acY_ua2e_fVqEcfxMBe5wnjue/pub?gid=0&single=true&output=csv"
df = pd.read_csv(sheet_url)

# Materiály (TOTO CHÝBALO NA ZAČIATKU)
material_sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQf4EiqZt1grkazJgfYWVhG0M8FGLNCjaGk6dcXhO3r04JQuZ9Qxv1jelDo3c8hBLy7Ny5C1pZqvbfS/pub?output=csv"
df_mat = pd.read_csv(material_sheet_url)

# --- 3. RIADOK S ATRIBÚTMI (Zákazník) ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    datum = st.date_input("Dátum", datetime.date.today())

with col2:
    ponuka = st.text_input("Označenie CP")

zoznam_zakaznikov = sorted(df['zakaznik'].unique())
moznosti_zakaznikov = ["+ Pridať nového zákazníka"] + zoznam_zakaznikov

with col3:
    vyber = st.selectbox("Názov Zákazníka", moznosti_zakaznikov)

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwNR33wxSNXJFo9-o2otM-mdKQE22s3i3y5n08dY7eogGhhKDTasiPn3zaOoSihppTq/exec"

if vyber == "+ Pridať nového zákazníka":
    with col3:
        zakaznik = st.text_input("Zadajte meno nového zákazníka", key="new_cust_name")
    with col4:
        krajina_hodnota = st.text_input("Krajina Zákazníka (manuálne)", key="new_cust_country")
        lojalita = 0.5
    with col3:
        if st.button("💾 Uložiť do databázy", type="primary", use_container_width=True):
            if zakaznik.strip() and krajina_hodnota.strip():
                try:
                    res = requests.post(WEB_APP_URL, json={"zakaznik": zakaznik, "krajina": krajina_hodnota})
                    if res.status_code == 200:
                        st.success("Uložené!"); st.cache_data.clear()
                    else: st.error("Chyba servera")
                except: st.error("Spojenie zlyhalo")
else:
    data_zakaznika = df[df['zakaznik'] == vyber].iloc[0]
    zakaznik = vyber
    krajina_hodnota = str(data_zakaznika['krajina'])
    lojalita = float(data_zakaznika['lojalita'])
    with col4:
        st.text_input("Krajina Zákazníka", value=krajina_hodnota, disabled=True)

st.divider()

# --- 5. RIADOK: POLOŽKA (ITEM) ---
col5, col6, col7, col8, col9, col10, col11, col12 = st.columns(8)

with col5:
    item = st.text_input("ITEM", key="item_input")
with col6:
    pocet_kusov = st.number_input("Počet kusov", min_value=1, value=1, key="pocet_input")
with col7:
    narocnost = st.selectbox("Náročnosť", options=[1, 2, 3, 4, 5], key="narocnost_input")
with col8:
    tvar_item = st.selectbox("Tvar položky", options=["STV", "KR"], key="tvar_input")

if tvar_item == "KR":
    with col9: d = st.number_input("D(mm)", min_value=0.0, format="%.1f", key="d_kr")
    with col10: l = st.number_input("L(mm)", min_value=0.0, format="%.1f", key="l_kr")
    s, v = 0.0, 0.0
else:
    with col9: d = st.number_input("D/P(mm)", min_value=0.0, format="%.1f", key="d_stv")
    with col10: s = st.number_input("S(mm)", min_value=0.0, format="%.1f", key="s_stv")
    with col11: v = st.number_input("V(mm)", min_value=0.0, format="%.1f", key="v_stv")
    l = 0.0

st.divider()

# --- 6. RIADOK: MATERIÁL, AKOSŤ, POLOTOVAR ---
WEB_APP_MAT_URL = "https://script.google.com/macros/s/AKfycbzyZxjTplhk010oq7ozvovAGx5lRx72PjqUvoJUrNazx_jRfq7lqfQgbeHYG9O-NCcX/exec"

col_m1, col_m2, col_m3 = st.columns(3)

with col_m1:
    zoznam_materialov = sorted(df_mat['material'].unique())
    material = st.selectbox("Materiál", zoznam_materialov, key="mat_select")

with col_m2:
    filtr_akosti = df_mat[df_mat['material'] == material]
    zoznam_akosti = ["+ Pridať novú akosť"] + sorted(filtr_akosti['akost'].unique())
    vyber_akosti = st.selectbox("Akosť", zoznam_akosti, key="akost_select")

with col_m3:
    # Polotovar teraz berie unikátne tvary z vopred načítaného df_mat
    polotovar = st.selectbox("Tvar Polotovaru", sorted(df_mat['tvar'].unique()), key="polo_vsetky")

if vyber_akosti == "+ Pridať novú akosť":
    st.info(f"✨ Nová akosť pre: {material}")
    c_n1, c_n2, c_n3, c_n4, c_n5, c_n6 = st.columns(6)
    with c_n1: nova_akost = st.text_input("Názov akosti")
    with c_n2: nova_cena = st.number_input("Cena (€/kg)", min_value=0.0, format="%.2f")
    with c_n3: novy_tvar_zapis = st.selectbox("Tvar pre zápis", sorted(df_mat['tvar'].unique()), key="nz_tvar")
    with c_n4: r1 = st.number_input("R1", min_value=0.0)
    with col_m3: pass # rezervované
    with c_n5: r2 = st.number_input("R2", min_value=0.0)
    with c_n6: r3 = st.number_input("R3", min_value=0.0)

    if st.button("💾 Uložiť novú akosť", type="primary"):
        if nova_akost.strip():
            nova_data = {"Názov": item, "Akost": nova_akost, "Material": material, "Cena": nova_cena, "Tvar": novy_tvar_zapis, "Rozmer1": r1, "Rozmer2": r2, "Rozmer3": r3}
            try:
                response = requests.post(WEB_APP_MAT_URL, json=nova_data)
                if response.status_code == 200:
                    st.success("Uložené!"); st.cache_data.clear()
                else: st.error(f"Chyba {response.status_code}")
            except Exception as e: st.error(f"Chyba: {e}")
    akost = nova_akost
else:
    akost = vyber_akosti
