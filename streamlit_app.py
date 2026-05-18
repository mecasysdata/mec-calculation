import streamlit as st
import pandas as pd
import datetime
import re
import math

# --- 1. CONFIG & ŠTÝL ---
st.set_page_config(layout="wide", page_title="MEC Calculation")

# --- DOPLNENÝ POMOCNÝ MECHANIZMUS PRE KOŠÍK ---
if "kosik" not in st.session_state:
    st.session_state.kosik = []

# --- DOPLNENÝ POMOCNÝ MECHANIZMUS PRE INTELIGENTNÝ RESET ITEMU ---
if "stary_item" not in st.session_state:
    st.session_state.stary_item = ""

# Sledujeme aktuálnu hodnotu v URL parametri/skrytom stave pred vykreslením
if "aktualny_pocet_kusov" not in st.session_state:
    st.session_state.aktualny_pocet_kusov = 1

# Inicializácia stavov pre AI modely
if "cas_potvrdeny" not in st.session_state:
    st.session_state.cas_potvrdeny = False
if "schvaleny_cas" not in st.session_state:
    st.session_state.schvaleny_cas = 3.0

# --- 2. CACHING (Sťahovanie dát len raz) ---
@st.cache_data(ttl=600)  # Dáta sa držia v pamäti 10 minút
def load_data_from_url(url):
    try:
        data = pd.read_csv(url)
        # Vyčistíme názvy stĺpcov od bielych znakov a prevedieme na lowercase pre konzistenciu
        data.columns = data.columns.str.strip().str.lower()
        return data
    except Exception as e:
        st.error(f"Chyba pri načítavaní dát z URL: {e}")
        return pd.DataFrame()

# --- NAČÍTANIE ZDROJOV ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSuHQWbpryWNerWr8aKKheHbzTPhXI6lS7YH1sL5zwFIIzLfpTZz47acY_ua2e_fVqEcfxMBe5wnjue/pub?gid=0&single=true&output=csv"
MATERIAL_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQf4EiqZt1grkazJgfYWVhG0M8FGLNCjaGk6dcXhO3r04JQuZ9Qxv1jelDo3c8hBLy7Ny5C1pZqvbfS/pub?output=csv"
SHEET_KOOP_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRfPBZ4TCpQyiqybU0ADu3AMwHCi2qOKifQAOnnTWnorVNJ1SVxtN6zJzXthOxCVwtXWp__Bp_-nto0/pub?gid=1180392224&single=true&output=csv"

df = load_data_from_url(SHEET_URL)
df_mat = load_data_from_url(MATERIAL_SHEET_URL)
df_koop = load_data_from_url(SHEET_KOOP_URL)

# Ak sú dáta prázdne, zastavíme aplikáciu elegantne, nie crasm
if df.empty or df_mat.empty or df_koop.empty:
    st.error("Kritické dáta nie sú dostupné. Skontrolujte pripojenie na Google Sheets.")
    st.stop()

# --- 3. LOGO A NÁZOV ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    try: st.image("logo.png", width=150)
    except: st.write("🖼️ Logo")
with col_title:
    st.title("MEC Calculation")

st.divider()

# --- 4. ZÁKAZNÍK (Defenzívna logika) ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    datum = st.date_input("Dátum", datetime.date.today())
with col2:
    ponuka = st.text_input("Označenie CP")

# Predpokladáme, že stĺpec v sheet_url sa volá 'zakaznik' (po našom lower() čistení)
zoznam_zakaznikov = sorted(df['zakaznik'].dropna().unique()) if 'zakaznik' in df.columns else []
moznosti_zakaznikov = ["+ Pridať nového zákazníka"] + zoznam_zakaznikov

with col3:
    vyber = st.selectbox("Názov Zákazníka", moznosti_zakaznikov)

zakaznik = ""
krajina_hodnota = ""
lojalita = 0.5

if vyber == "+ Pridať nového zákazníka":
    with col3: 
        zakaznik = st.text_input("Meno nového zákazníka", key="new_cust_name")
    with col4:
        krajina_hodnota = st.text_input("Krajina Zákazníka (manuálne)", key="new_cust_country")
else:
    # Bezpečné vytiahnutie riadku bez .iloc[0] na prázdno
    filter_zak = df[df['zakaznik'] == vyber]
    if not filter_zak.empty:
        data_zakaznika = filter_zak.iloc[0]
        zakaznik = vyber
        krajina_hodnota = str(data_zakaznika.get('krajina', 'Neznáma'))
        lojalita = float(data_zakaznika.get('lojalita', 0.5))
    else:
        st.warning(f"Zákazník {vyber} nemá v tabuľke priradené dáta.")
    
    with col4: 
        st.text_input("Krajina Zákazníka", value=krajina_hodnota, disabled=True, key="disabled_country")

st.divider()

# --- 5. ITEM GEOMETRIA ---
col5, col6, col7, col8, col9, col10, col11 = st.columns(7)

with col5: 
    item = st.text_input("ITEM", key="item_input")

# --- DETEKCIA ZMENY AKTUÁLNEHO ITEMU ---
if item != st.session_state.stary_item:
    if st.session_state.stary_item != "":
        # Užívateľ prepísal ITEM -> úplný reset všetkých polí od ITEM nadol
        st.session_state.aktualny_pocet_kusov = 1
        st.session_state.stary_item = item
        
        # Odstránime kľúče z pamäte, aby sa widgety vykreslili čisté a prázdne
        kluce_na_vymazanie = ["pocet_input", "narocnost_input", "tvar_input", "d_kr", "l_kr", "d_stv", "s_stv", "v_stv", "mat_select", "akost_multi", "man_akost_chk", "polo_inteligent", "koop_main_checkbox", "manual_rho", "mat_k", "druh_k", "vystupny_cas_input"]
        for klic in kluce_na_vymazanie:
            if klic in st.session_state:
                del st.session_state[klic]
        
        # Reset stavov pre AI model
        st.session_state.cas_potvrdeny = False
        st.session_state.schvaleny_cas = 3.0
        st.rerun()
    else:
        st.session_state.stary_item = item
else:
    pass

with col6: 
    # Počet kusov načítava hodnotu dynamicky, aby sa dal vymazať nezávisle od reštartu
    predvoleny_pocet = st.session_state.aktualny_pocet_kusov
    pocet_kusov = st.number_input("Počet kusov", min_value=1, value=int(predvoleny_pocet), key="pocet_input")
    st.session_state.aktualny_pocet_kusov = pocet_kusov

with col7: narocnost = st.selectbox("Náročnosť", options=[1, 2, 3, 4, 5], key="narocnost_input")
with col8: tvar_item = st.selectbox("Tvar položky", options=["STV", "KR"], key="tvar_input")

d, l, s, v = 0.0, 0.0, 0.0, 0.0
if tvar_item == "KR":
    with col9: d = st.number_input("D(mm)", min_value=0.0, format="%.1f", key="d_kr")
    with col10: l = st.number_input("L(mm)", min_value=0.0, format="%.1f", key="l_kr")
else:
    with col9: d = st.number_input("D/P(mm)", min_value=0.0, format="%.1f", key="d_stv")
    with col10: s = st.number_input("S(mm)", min_value=0.0, format="%.1f", key="s_stv")
    with col11: v = st.number_input("V(mm)", min_value=0.0, format="%.1f", key="v_stv")

st.divider()

# --- 6. MATERIÁL A POLOTOVAR ---
def get_sorted_dims(a, b, c):
    try: return sorted([float(a), float(b), float(c)], reverse=True)
    except: return [0.0, 0.0, 0.0]

col_m1, col_m2, col_m3 = st.columns([2, 3, 3])

with col_m1:
    zoznam_materialov = sorted(df_mat['material'].dropna().unique()) if 'material' in df_mat.columns else []
    material_vyber = st.selectbox("Materiál", zoznam_materialov, key="mat_select")

with col_m2:
    df_f_akost = df_mat[df_mat['material'] == material_vyber]
    filtr_akosti_vsetky = sorted(df_f_akost['akost'].dropna().astype(str).unique()) if 'akost' in df_f_akost.columns else []
    akost_vyber_list = st.multiselect("Výber akostí", options=filtr_akosti_vsetky, key="akost_multi")
    manual_akost_check = st.checkbox("+ Iná akosť (manuálne)", key="man_akost_chk")

vhodne_moznosti = []
if manual_akost_check:
    zoznam_na_vyber = ["+ Pridať nový/iný polotovar"]
else:
    df_relevant = df_mat[(df_mat['material'] == material_vyber) & (df_mat['akost'].astype(str).isin(akost_vyber_list))].copy()
    
    if tvar_item == "KR" and 'názov' in df_relevant.columns:
        df_relevant = df_relevant[df_relevant['názov'].str.contains('KR|6HR|TR', case=False, na=False)]

    if not df_relevant.empty and all(col in df_relevant.columns for col in ['rozmer1', 'rozmer2', 'rozmer3']):
        df_relevant['sort_key'] = df_relevant.apply(lambda r: get_sorted_dims(r['rozmer1'], r['rozmer2'], r['rozmer3']), axis=1)
        df_relevant = df_relevant.sort_values(by='sort_key')
        
        for idx, r in df_relevant.iterrows():
            label = f"[{r.get('akost', '')}] {r.get('názov', '')} | {r.get('rozmer1', 0)}x{r.get('rozmer2', 0)}x{r.get('rozmer3', 0)} | Cena: {r.get('cena', 0)}€/bm"
            vhodne_moznosti.append({"label": label, "cena": float(r.get('cena', 0)), "akost_povodna": str(r.get('akost', ''))})
            
    zoznam_na_vyber = [item['label'] for item in vhodne_moznosti] + ["+ Pridať nový/iný polotovar"]

with col_m3:
    idx_start = len(zoznam_na_vyber) - 1 if (manual_akost_check or not vhodne_moznosti) else 0
    vybrany_polo_str = st.selectbox("Výber polotovaru (zoznam)", zoznam_na_vyber, index=idx_start, key="polo_inteligent")

cena_polotovaru = 0.0
relevantna_akost = ""

if vybrany_polo_str == "+ Pridať nový/iný polotovar":
    c_n1, c_n2, c_n3 = st.columns(3)
    with c_n1:
        povodna_akost_val = akost_vyber_list[0] if akost_vyber_list else ""
        nova_akost = st.text_input("Názov akosti", value="" if manual_akost_check else povodna_akost_val, key="input_nov_akost")
    with c_n2:
        cena_polotovaru = st.number_input("Cena (€/bm)", min_value=0.0, format="%.2f", key="input_nov_cena")
    with c_n3:
        nazov_pol = st.text_input("Názov polotovaru", value="MANUAL", key="input_nov_nazov")
    relevantna_akost = nova_akost.upper().replace(" ", "").strip()
else:
    vybrany_objekt = next((item for item in vhodne_moznosti if item['label'] == vybrany_polo_str), None)
    if vybrany_objekt:
        cena_polotovaru = vybrany_objekt['cena']
        relevantna_akost = vybrany_objekt['akost_povodna'].upper().replace(" ", "").strip()

dlzka_pre_vypocet = l if tvar_item == "KR" else d
cena_mat_kus = (dlzka_pre_vypocet / 1000) * cena_polotovaru

# --- 7. KLASIFIKÁCIA MECASYS ---
def get_mecasys_logic(cat, akost_str):
    sub = "OSTATNÉ"
    rho = 0.0
    if not akost_str: return sub, rho
    match = re.
