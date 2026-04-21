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

# --- 3. NAČÍTANIE DÁT (Zákazníci) ---
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSuHQWbpryWNerWr8aKKheHbzTPhXI6lS7YH1sL5zwFIIzLfpTZz47acY_ua2e_fVqEcfxMBe5wnjue/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame(columns=['zakaznik', 'krajina', 'lojalita'])

df_zakaznici = load_data(sheet_url)

# Zoznam mien pre selectbox
zoznam_mien = sorted(df_zakaznici['zakaznik'].unique().tolist())
moznost_novy = "Nový zákazník (zadať ručne)"
if moznost_novy not in zoznam_mien:
    zoznam_mien.append(moznost_novy)

# --- 4. HLAVNÝ RIADOK ---
# c1: Dátum, c2: Označenie, c3: Dynamická časť zákazníka
c1, c2, c3 = st.columns([1, 1.2, 6])

with c1:
    st.date_input("Dátum")

with c2:
    st.text_input("Označenie CP", placeholder="napr. CP-001")

with c3:
    # Najskôr určíme, koho ideme zobraziť (kvôli indexu v selectboxe)
    # Ak sme v session_state uložili meno nového, nájdeme jeho pozíciu
    target_customer = st.session_state.get("last_added", zoznam_mien[0])
    try:
        idx = zoznam_mien.index(target_customer)
    except:
        idx = 0

    # Rozdelíme c3 na stĺpce pre Selectbox a detaily
    sub_select, sub_detail = st.columns([2, 4])

    with sub_select:
        vyber = st.selectbox("Zákazník", options=zoznam_mien, index=idx, key="main_select")

    with sub_detail:
        if vyber == moznost_novy:
            # --- MÓD: ZADÁVANIE NOVÉHO ---
            n1, n2, n3, n4 = st.columns([1.5, 1, 0.7, 0.8])
            with n1: novy_meno = st.text_input("Meno", key="n1")
            with n2: novy_krajina = st.text_input("Krajina", key="n2")
            with n3: st.text_input("Lojalita", value="0.5", disabled=True)
            with n4:
                st.write(" ")
                if st.button("Uložiť"):
                    if novy_meno and novy_krajina:
                        api = "https://script.google.com/macros/s/AKfycbwNR33wxSNXJFo9-o2otM-mdKQE22s3i3y5n08dY7eogGhhKDTasiPn3zaOoSihppTq/exec"
                        requests.post(api, json={"zakaznik": novy_meno, "krajina": novy_krajina, "lojalita": 0.5})
                        # TOTO JE TRIK: Uložíme meno do session_state a povieme mu, nech sa vyberie
                        st.session_state["last_added"] = novy_meno
                        st.rerun()
            
            final_zakaznik, final_krajina, final_lojalita = novy_meno, novy_krajina, 0.5
        
        else:
            # --- MÓD: ZOBRAZENIE EXISTUJÚCEHO ---
            v1, v2 = st.columns([1, 1])
            row = df_zakaznici[df_zakaznici['zakaznik'] == vyber]
            if not row.empty:
                res_krajina = str(row['krajina'].values[0])
                # Vyčistenie lojality na číslo
                l_raw = str(row['lojalita'].values[0])
                try: res_lojalita = float(re.sub(r'[^0-9.]', '', l_raw.replace(',', '.')))
                except: res_lojalita = 0.5
            else:
                res_krajina, res_lojalita = "---", 0.5
            
            with v1: st.text_input("Krajina", value=res_krajina, disabled=True, key="v1")
            with v2: st.text_input("Lojalita", value=res_lojalita, disabled=True, key="v2")
            
            final_zakaznik, final_krajina, final_lojalita = vyber, res_krajina, res_lojalita

st.divider()

# --- 6. RIADOK PRE POLOŽKU (Všetko v jednom) ---

# Definujeme veľa stĺpcov, aby sa to zmestilo: 
# Item | Náročnosť | KS | Tvar | Rozmer1 | Rozmer2 | Rozmer3
cols = st.columns([2, 0.8, 0.8, 1, 0.8, 0.8, 0.8])

with cols[0]:
    item_nazov = st.text_input("ITEM", placeholder="Názov komponentu")

with cols[1]:
    narocnost = st.selectbox("Náročnosť", options=[1, 2, 3, 4, 5])

with cols[2]:
    pocet_ks = st.number_input("KS", min_value=1, step=1, value=1)

with cols[3]:
    tvar = st.selectbox("Tvar", options=["KR", "STV"])

# Dynamické rozmery v stĺpcoch 4, 5 a 6
rozmer_D = 0.0
rozmer_L = 0.0
rozmer_S = 0.0
rozmer_V = 0.0

if tvar == "KR":
    with cols[4]:
        rozmer_D = st.number_input("D (mm)", min_value=0.0, format="%.2f")
    with cols[5]:
        rozmer_L = st.number_input("L (mm)", min_value=0.0, format="%.2f")
    with cols[6]:
        # Prázdne pole, aby línia pokračovala
        st.write("")

elif tvar == "STV":
    with cols[4]:
        rozmer_D = st.number_input("D/P (mm)", min_value=0.0, format="%.2f")
    with cols[5]:
        rozmer_S = st.number_input("S (mm)", min_value=0.0, format="%.2f")
    with cols[6]:
        rozmer_V = st.number_input("V (mm)", min_value=0.0, format="%.2f")

st.divider()
# --- 8. NAČÍTANIE SHEETU MATERIÁLOV (Hustoty) ---
sheet_hustoty_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRcCPwLT_Cm8Xpj4urw7DUa5FGGyWiCEKKl8ySUEnGtFjsKzbvwtw6MURs1TyqasHhAJsWcdP6d3Q7O/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_material_data(url):
    try:
        data = pd.read_csv(url)
        data.columns = data.columns.str.strip()
        for col in ['material', 'akost']:
            if col in data.columns:
                data[col] = data[col].astype(str).str.strip()
        return data
    except:
        return pd.DataFrame(columns=['material', 'akost', 'hustota'])

df_materialy = load_material_data(sheet_hustoty_url)

# --- 9. SEKCIA MATERIÁL A HUSTOTA ---
st.subheader("Materiál a fyzikálne vlastnosti")
m_col1, m_col2, m_col3 = st.columns([2, 2, 2])

with m_col1:
    seznam_materialov = sorted(df_materialy['material'].unique())
    material = st.selectbox("Materiál", options=seznam_materialov, key="sel_mat")

with m_col2:
    seznam_akosti = list(sorted(df_materialy[df_materialy['material'] == material]['akost'].unique()))
    if "Iná akosť (zadať ručne)" not in seznam_akosti:
        seznam_akosti.append("Iná akosť (zadať ručne)")
    
    akost_vyber = st.selectbox("Akosť", options=seznam_akosti, key="sel_akost")

# Logika pre určenie názvu akosti a hustoty
hustota_auto = 0.0
akost_finalna = ""

if akost_vyber == "Iná akosť (zadať ručne)":
    akost_finalna = st.text_input("Zadajte názov novej akosti:", key="n_akost_text")
else:
    akost_finalna = akost_vyber


