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
# SEKCIA 8: FINÁLNA KALKULÁCIA MATERIÁLU A DYNAMICKÝ SKLAD
# ==============================================================================
st.divider()
st.subheader("📋 Kalkulácia materiálu")

# Načítanie skladu
sheet_sklad_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQf4EiqZt1grkazJgfYWVhG0M8FGLNCjaGk6dcXhO3r04JQuZ9Qxv1jelDo3c8hBLy7Ny5C1pZqvbfS/pub?output=csv"

@st.cache_data(ttl=5)
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
    # 1. VÝBER MATERIÁLU (Z tvojej predošlej sekcie)
    st.info(f"Aktuálna kategória: **{material}**")
    
    # 2. VÝBER AKOSTI (Len tie, ktoré patria k materiálu)
    df_kat = df_sklad[df_sklad['Material'] == material]
    dostupne_akosti = sorted(df_kat['Akost'].unique().tolist())
    
    col_akost, col_tvar = st.columns(2)
    with col_akost:
        vybrana_akost_sklad = st.selectbox("Vyberte akosť:", options=["-- Vybrať --"] + dostupne_akosti)
    
    if vybrana_akost_sklad != "-- Vybrať --":
        # 3. VÝBER KONKRÉTNEHO ROZMERU
        df_akost = df_kat[df_kat['Akost'] == vybrana_akost_sklad].copy()
        df_akost['rozmer_text'] = df_akost.apply(lambda r: f"{r['Názov']} ({r['Rozmer1']}x{r['Rozmer2']}x{r['Rozmer3']})", axis=1)
        
        polotovary_list = df_akost.to_dict('records')
        vybrany_polotovar = st.selectbox("Vyberte rozmer polotovaru:", 
                                         options=polotovary_list + [{"rozmer_text": "➕ Iný (Pridať nový...)"}],
                                         format_func=lambda x: x['rozmer_text'])

        # PRÍPAD A: POLOTOVAR EXISTUJE
        if vybrany_polotovar and vybrany_polotovar['rozmer_text'] != "➕ Iný (Pridať nový...)":
            # Kontrola rozmerov
            def check_dims(row):
                s = sorted([float(row['Rozmer1']), float(row['Rozmer2']), float(row['Rozmer3'])], reverse=True)
                z = sorted([float(rozmer_D), float(rozmer_S), float(rozmer_V)], reverse=True)
                return all(s[i] >= z[i] for i in range(len([v for v in z if v > 0])))

            if check_dims(vybrany_polotovar):
                st.success("✅ Rozmerovo vyhovuje")
                potvrdit = st.button("✅ Potvrdiť materiál a zobraziť cenu")
                
                if potvrdit:
                    c_m = float(vybrany_polotovar['Cena'])
                    c_ks = c_m * (rozmer_L / 1000)
                    
                    st.divider()
                    res1, res2, res3 = st.columns([2, 1, 1])
                    with res1: st.write(f"📦 Polotovar: **{vybrany_polotovar['Názov']}**")
                    with res2: st.write(f"📏 Cena: **{c_m:.2f} €/m**")
                    with res3: st.write(f"💰 Cena/ks: **{c_ks:.2f} €**")
            else:
                st.error("❌ Polotovar je prísliš malý pre zadanie!")

        # PRÍPAD B: PRIDANIE NOVÉHO (Ak nič nesedí)
        else:
            st.warning("Zadajte parametre pre nový polotovar:")
            with st.container():
                # Všetky stĺpce zo sheetu
                r1_1, r1_2, r1_3, r1_4 = st.columns(4)
                with r1_1: new_n = st.text_input("Názov (B)")
                with r1_2: new_a = st.text_input("Akosť (C)", value=vybrana_akost_sklad)
                with r1_3: new_m = st.text_input("Materiál (D)", value=material)
                with r1_4: new_c = st.number_input("Cena €/m (E)", min_value=0.0, step=0.1)
                
                r2_1, r2_2, r2_3, r2_4 = st.columns(4)
                with r2_1: new_t = st.selectbox("Tvar (F)", ["KR", "6HR", "STV", "RÚR", "PLECH"])
                with r2_2: new_r1 = st.number_input("Rozmer 1 (G)", min_value=0.0)
                with r2_3: new_r2 = st.number_input("Rozmer 2 (H)", min_value=0.0)
                with r2_4: new_r3 = st.number_input("Rozmer 3 (I)", min_value=0.0)

                if st.button("💾 Uložiť do sheetu a použiť"):
                    if new_n and new_c > 0:
                        API = "https://script.google.com/macros/s/AKfycbzyZxjTplhk010oq7ozvovAGx5lRx72PjqUvoJUrNazx_jRfq7lqfQgbeHYG9O-NCcX/exec"
                        payload = {
                            "Názov": new_n, "Akost": new_a, "Material": new_m,
                            "Cena": new_c, "Tvar": new_t, "Rozmer1": new_r1,
                            "Rozmer2": new_r2, "Rozmer3": new_r3
                        }
                        try:
                            requests.post(API, json=payload, timeout=10)
                            st.success(f"Uložené! Cena: {new_c:.2f} €/m | Na kus: {(new_c * (rozmer_L/1000)):.2f} €")
                            st.cache_data.clear()
                            # Tu sa zobrazí cena hneď po uložení
                            res1, res2, res3 = st.columns([2, 1, 1])
                            with res1: st.write(f"📦 Nový: **{new_n}**")
                            with res2: st.write(f"📏 Cena: **{new_c:.2f} €/m**")
                            with res3: st.write(f"💰 Cena/ks: **{(new_c * (rozmer_L/1000)):.2f} €**")
                        except:
                            st.error("Chyba pri ukladaní.")
                    else:
                        st.error("Musíte vyplniť Názov a Cenu!")
# ==============================================================================

                else: st.error("Chýba akosť alebo cena!")

