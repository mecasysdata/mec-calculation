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

zoznam_mien = sorted(df_zakaznici['zakaznik'].unique().tolist())
moznost_novy = "Nový zákazník (zadať ručne)"
if moznost_novy not in zoznam_mien:
    zoznam_mien.append(moznost_novy)

# --- 4. HLAVNÝ RIADOK (Zákazník) ---
c1, c2, c3 = st.columns([1, 1.2, 6])

with c1:
    st.date_input("Dátum")

with c2:
    st.text_input("Označenie CP", placeholder="napr. CP-001")

with c3:
    target_customer = st.session_state.get("last_added", zoznam_mien[0])
    try: idx = zoznam_mien.index(target_customer)
    except: idx = 0

    sub_select, sub_detail = st.columns([2, 4])

    with sub_select:
        vyber = st.selectbox("Zákazník", options=zoznam_mien, index=idx, key="main_select")

    with sub_detail:
        if vyber == moznost_novy:
            n1, n2, n3, n4 = st.columns([1.5, 1, 0.7, 0.8])
            with n1: novy_meno = st.text_input("Meno", key="n1")
            with n2: novy_krajina = st.text_input("Krajina", key="n2")
            with n3: st.text_input("Lojalita", value="0.5", disabled=True)
            with n4:
                st.write(" ")
                if st.button("Uložiť", key="btn_save_cust"):
                    if novy_meno and novy_krajina:
                        api = "https://script.google.com/macros/s/AKfycbwNR33wxSNXJFo9-o2otM-mdKQE22s3i3y5n08dY7eogGhhKDTasiPn3zaOoSihppTq/exec"
                        requests.post(api, json={"zakaznik": novy_meno, "krajina": novy_krajina, "lojalita": 0.5})
                        st.session_state["last_added"] = novy_meno
                        st.rerun()
            final_zakaznik, final_krajina, final_lojalita = novy_meno, novy_krajina, 0.5
        
        else:
            v1, v2 = st.columns([1, 1])
            row = df_zakaznici[df_zakaznici['zakaznik'] == vyber]
            if not row.empty:
                res_krajina = str(row['krajina'].values[0])
                l_raw = str(row['lojalita'].values[0])
                try: res_lojalita = float(re.sub(r'[^0-9.]', '', l_raw.replace(',', '.')))
                except: res_lojalita = 0.5
            else:
                res_krajina, res_lojalita = "---", 0.5
            
            with v1: st.text_input("Krajina", value=res_krajina, disabled=True, key=f"kraj_{vyber}")
            with v2: st.text_input("Lojalita", value=res_lojalita, disabled=True, key=f"loj_{vyber}")
            final_zakaznik, final_krajina, final_lojalita = vyber, res_krajina, res_lojalita

st.divider()

# --- 6. RIADOK PRE POLOŽKU ---
cols = st.columns([2, 0.8, 0.8, 1, 0.8, 0.8, 0.8])

with cols[0]:
    item_nazov = st.text_input("ITEM", placeholder="Názov komponentu")
with cols[1]:
    narocnost = st.selectbox("Náročnosť", options=[1, 2, 3, 4, 5])
with cols[2]:
    pocet_ks = st.number_input("KS", min_value=1, step=1, value=1)
with cols[3]:
    tvar = st.selectbox("Tvar", options=["KR", "STV"])

rozmer_D, rozmer_L, rozmer_S, rozmer_V = 0.0, 0.0, 0.0, 0.0

if tvar == "KR":
    with cols[4]: rozmer_D = st.number_input("D (mm)", min_value=0.0, format="%.2f")
    with cols[5]: rozmer_L = st.number_input("L (mm)", min_value=0.0, format="%.2f")
elif tvar == "STV":
    with cols[4]: rozmer_D = st.number_input("D/P (mm)", min_value=0.0, format="%.2f")
    with cols[5]: rozmer_S = st.number_input("S (mm)", min_value=0.0, format="%.2f")
    with cols[6]: rozmer_V = st.number_input("V (mm)", min_value=0.0, format="%.2f")

st.divider()

# --- 7. MATERIÁL A HUSTOTA (Upravená sekcia s dynamickým riadkom) ---
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

# Layout riadku pre Materiál a Akosť
m_col1, m_col_rest = st.columns([2, 6.5])

with m_col1:
    seznam_materialov = sorted(df_materialy['material'].unique())
    material = st.selectbox("Materiál", options=seznam_materialov, key="sel_material_main")

with m_col_rest:
    # Definujeme stĺpce vnútri dynamicky podľa toho, či je vybraná "Iná akosť"
    seznam_akosti = list(sorted(df_materialy[df_materialy['material'] == material]['akost'].unique()))
    if "Iná akosť (zadať ručne)" not in seznam_akosti:
        seznam_akosti.append("Iná akosť (zadať ručne)")

    # Ak je vybraná Iná akosť, potrebujeme viac stĺpcov pre zadanie a uloženie
    if st.session_state.get("sel_akost_main") == "Iná akosť (zadať ručne)":
        sub_m1, sub_m2, sub_m3, sub_m4 = st.columns([1.5, 1.5, 1, 0.8])
        with sub_m1:
            akost_vyber = st.selectbox("Akosť", options=seznam_akosti, key="sel_akost_main")
        with sub_m2:
            akost_finalna = st.text_input("Zadať akosť", key="n_akost_input_text")
        # Výpočet hustoty_auto predtým než ju vložíme do inputu
        hustota_auto = 0.0
        if material == "NEREZ": hustota_auto = 8000.0
        elif material == "OCEĽ": hustota_auto = 7900.0
        
        with sub_m3:
            hustota = st.number_input("Hustota [kg/m3]", min_value=0.0, value=float(hustota_auto), format="%.2f", key="h_new_input")
        with sub_m4:
            st.write(" ")
            if st.button("Uložiť", key="btn_save_mat"):
                if akost_finalna and hustota > 0:
                    url_api_hustota = "https://script.google.com/macros/s/AKfycbysapIykA2JulM9882rQmM3tfFvbvrmYDeW-iM5jyR4MTg8ZlNWhTdgV4pGxNhn6JNb/exec"
                    try:
                        # Pridaná kontrola statusu
                        response = requests.post(url_api_hustota, json={"material": material, "akost": akost_finalna, "hustota": hustota}, timeout=10)
                        if response.status_code == 200:
                            st.success("Uložené!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Server vrátil chybu: {response.status_code}")
                    except Exception as e:
                        # Vypíše skutočnú chybu len ak nastane problém so spojením
                        st.error(f"Chyba spojenia!")
                else:
                    st.warning("Doplňte názov!")
    else:
        # Štandardné zobrazenie, keď je akosť v databáze
        sub_m1, sub_m2 = st.columns([2, 1])
        with sub_m1:
            akost_vyber = st.selectbox("Akosť", options=seznam_akosti, key="sel_akost_main")
            akost_finalna = akost_vyber
        
        # Logika hľadania hustoty pre existujúcu akosť
        hustota_auto = 0.0
        if material == "NEREZ": hustota_auto = 8000.0
        elif material == "OCEĽ": hustota_auto = 7900.0
        elif material == "FAREBNÉ KOVY":
            akost_test = str(akost_finalna).replace(',', '.')
            if akost_test.startswith("3.7"): hustota_auto = 4500.0
            elif akost_test.startswith("3."): hustota_auto = 2900.0
            elif akost_test.startswith("2."): hustota_auto = 9000.0
        elif material == "PLAST":
            hladana_akost = str(akost_finalna).strip().upper()
            df_temp = df_materialy.copy()
            df_temp['akost_up'] = df_temp['akost'].astype(str).str.strip().str.upper()
            zhoda = df_temp[(df_temp['material'] == "PLAST") & (df_temp['akost_up'] == hladana_akost)]
            if not zhoda.empty:
                raw_h = str(zhoda['hustota'].values[0])
                clean_h = raw_h.replace(',', '').replace(' ', '').replace('\xa0', '').strip()
                try: hustota_auto = float(clean_h)
                except: hustota_auto = 0.0
        
        with sub_m2:
            input_key = f"hustota_input_{material}_{akost_finalna}".replace(" ", "_")
            hustota = st.number_input("Hustota [kg/m3]", min_value=0.0, value=float(hustota_auto), format="%.2f", key=input_key)

# Validácia a stop
if not akost_finalna or hustota <= 0:
    st.warning("Pre pokračovanie vyberte materiál a skontrolujte hustotu.")
    st.stop()

st.divider()

# ==============================================================================
# ==============================================================================
# SEKCIA 8: TECHNICKÁ KALKULÁCIA MATERIÁLU (PODĽA TVARU A ROZMEROV)
# ==============================================================================
st.divider()
st.subheader("📦 Výber polotovaru a výpočet ceny")

# 1. POMOCNÁ LOGIKA PRE ROZMERY (Metóda obálky)
def get_dims_sorted(r1, r2, r3):
    try:
        vals = [float(r1), float(r2), float(r3)]
        return sorted([v for v in vals if v > 0], reverse=True)
    except: return []

# 2. NAČÍTANIE DÁT (Hárok1)
sheet_sklad_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQf4EiqZt1grkazJgfYWVhG0M8FGLNCjaGk6dcXhO3r04JQuZ9Qxv1jelDo3c8hBLy7Ny5C1pZqvbfS/pub?output=csv"

@st.cache_data(ttl=10)
def nacti_sklad_final(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        for col in ['Rozmer1', 'Rozmer2', 'Rozmer3', 'Cena']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except: return pd.DataFrame()

df_sklad = nacti_sklad_final(sheet_sklad_url)

if not df_sklad.empty:
    # --- KROK 1: VÝBER PARAMETROV (Tvar -> Materiál -> Akosť) ---
    c1, c2, c3 = st.columns(3)
    
    with c1:
        # Tvoj definovaný zoznam tvarov
        zoznam_tvarov = ["6HR", "4HR", "I", "U", "L", "TR", "KR", "PL", "JAKL", "T"]
        vybrany_tvar = st.selectbox("Tvar polotovaru:", options=zoznam_tvarov)
        
    with c2:
        # Filtrujeme dostupné materiály pre tento tvar
        mats_v_tvare = sorted(df_sklad[df_sklad['Tvar'] == vybrany_tvar]['Material'].unique().tolist())
        v_mat = st.selectbox("Materiál:", options=mats_v_tvare if mats_v_tvare else [material])
        
    with c3:
        # Filtrujeme akosti pre tento tvar a materiál
        aks_v_tvare = sorted(df_sklad[(df_sklad['Tvar'] == vybrany_tvar) & (df_sklad['Material'] == v_mat)]['Akost'].unique().tolist())
        v_akost = st.selectbox("Akosť:", options=aks_v_tvare if aks_v_tvare else [akost_finalna])

    # --- KROK 2: LOGIKA ROZMEROV ---
    # Rozmery dielu (to, čo chce technológ vyrobiť)
    diel_dims = get_dims_sorted(rozmer_D, rozmer_S, rozmer_V)
    
    # Filtrujeme položky skladu, ktoré presne sedia na Tvar, Materiál a Akosť
    df_potencial = df_sklad[
        (df_sklad['Tvar'] == vybrany_tvar) & 
        (df_sklad['Material'] == v_mat) & 
        (df_sklad['Akost'] == v_akost)
    ].copy()

    vhodne_moznosti = []
    for _, row in df_potencial.iterrows():
        sklad_dims = get_dims_sorted(row['Rozmer1'], row['Rozmer2'], row['Rozmer3'])
        
        # Porovnanie: Musí mať dosť rozmerov a každý musí byť väčší alebo rovný dielu
        if len(sklad_dims) >= len(diel_dims):
            if all(sklad_dims[i] >= diel_dims[i] for i in range(len(diel_dims))):
                odpad = sum(sklad_dims) - sum(diel_dims)
                label = f"{row['Názov']} ({'x'.join(map(str, sklad_dims))} mm)"
                vhodne_moznosti.append({
                    "label": label, 
                    "cena_m": float(row['Cena']), 
                    "odpad": odpad,
                    "nazov": row['Názov']
                })

    # Zoradenie podľa najmenšieho odpadu
    vhodne_moznosti = sorted(vhodne_moznosti, key=lambda x: x['odpad'])

    # --- KROK 3: VÝBER A ZOBRAZENIE CIEN ---
    if vhodne_moznosti:
        vyber = st.selectbox("Dostupné rozmery (od najvhodnejšieho):", 
                             options=vhodne_moznosti + [{"label": "➕ Iný (Pridať nový...)"}],
                             format_func=lambda x: x['label'])

        if vyber['label'] != "➕ Iný (Pridať nový...)":
            st.success(f"✅ Rozmer vyhovuje pre diel {' x '.join(map(str, diel_dims))} mm")
            
            # Výpočty
            c_m = vyber['cena_m']
            c_ks = c_m * (rozmer_L / 1000)
            c_celkom = c_ks * pocet_ks
            
            # Zobrazenie výsledkov v jednom riadku
            st.write("---")
            r1, r2, r3 = st.columns([2, 1, 1])
            with r1: st.write(f"💎 Polotovar: **{vyber['nazov']}**")
            with r2: st.write(f"📏 Cena: **{c_m:.2f} €/m**")
            with r3: st.write(f"📦 Cena/ks: **{c_ks:.2f} €**")
            st.info(f"Celková cena za {pocet_ks} ks: **{c_celkom:.2f} €**")
    else:
        st.warning(f"❌ V sklade nie je vhodný rozmer pre {vybrany_tvar} {v_mat} {v_akost}.")

    # --- KROK 4: FORMULÁR PRE NOVÝ POLOTOVAR (ak nič nesedí) ---
    with st.expander("➕ Pridať nový polotovar do skladu"):
        st.write("Vyplňte všetky údaje pre nový záznam:")
        f1, f2, f3, f4 = st.columns(4)
        with f1: n_nazov = st.text_input("Názov (B)")
        with f2: n_akost = st.text_input("Akosť (C)", value=v_akost)
        with f3: n_mat = st.text_input("Materiál (D)", value=v_mat)
        with f4: n_cena = st.number_input("Cena €/m (E)", min_value=0.0)
        
        f5, f6, f7, f8 = st.columns(4)
        with f5: n_tvar = st.selectbox("Tvar (F)", options=zoznam_tvarov, index=zoznam_tvarov.index(vybrany_tvar))
        with f6: n_r1 = st.number_input("Rozmer 1 (G)")
        with f7: n_r2 = st.number_input("Rozmer 2 (H)")
        with f8: n_r3 = st.number_input("Rozmer 3 (I)")

        if st.button("🚀 Uložiť a použiť cenu"):
            if n_nazov and n_cena > 0:
                API_URL = "https://script.google.com/macros/s/AKfycbzyZxjTplhk010oq7ozvovAGx5lRx72PjqUvoJUrNazx_jRfq7lqfQgbeHYG9O-NCcX/exec"
                payload = {
                    "Názov": n_nazov, "Akost": n_akost, "Material": n_mat,
                    "Cena": n_cena, "Tvar": n_tvar, "Rozmer1": n_r1,
                    "Rozmer2": n_r2, "Rozmer3": n_r3
                }
                requests.post(API_URL, json=payload)
                st.success(f"Uložené! Cena/m: {n_cena:.2f} € | Cena/ks: {(n_cena * (rozmer_L/1000)):.2f} €")
                st.cache_data.clear()

