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

# --- 6. RIADOK: MATERIÁL, AKOSŤ A INTELIGENTNÝ POLOTOVAR (LOGIKA PRE INÚ AKOSŤ) ---
# --- 6. RIADOK: MATERIÁL A POLOTOVAR (S CENAMI V JEDNOM RIADKU) ---
WEB_APP_MAT_URL = "https://script.google.com/macros/s/AKfycbzyZxjTplhk010oq7ozvovAGx5lRx72PjqUvoJUrNazx_jRfq7lqfQgbeHYG9O-NCcX/exec"
df_mat.columns = [c.lower().strip() for c in df_mat.columns]

def get_sorted_dims(a, b, c):
    try: return sorted([float(a), float(b), float(c)], reverse=True)
    except: return [0.0, 0.0, 0.0]

# TU JE ZMENA: Rozdelenie riadku na 5 stĺpcov
col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns([2, 2, 3, 1.2, 1.2])

with col_m1:
    zoznam_materialov = sorted(df_mat['material'].unique())
    material_vyber = st.selectbox("Materiál", zoznam_materialov, key="mat_select")

with col_m2:
    filtr_akosti = df_mat[df_mat['material'] == material_vyber]
    zoznam_akosti = sorted(filtr_akosti['akost'].unique()) + ["+ Iná akosť (zadať manuálne)"]
    akost_vyber = st.selectbox("Akosť", zoznam_akosti, key="akost_select")

vhodne_moznosti = []
if akost_vyber == "+ Iná akosť (zadať manuálne)":
    zoznam_na_vyber = ["+ Pridať nový/iný polotovar"]
else:
    df_relevant = df_mat[(df_mat['material'] == material_vyber) & (df_mat['akost'] == akost_vyber)].copy()
    if not df_relevant.empty:
        df_relevant['sort_key'] = df_relevant.apply(lambda r: get_sorted_dims(r['rozmer1'], r['rozmer2'], r['rozmer3']), axis=1)
        df_relevant = df_relevant.sort_values(by='sort_key')
    for idx, r in df_relevant.iterrows():
        label = f"{r['názov']} | {r['rozmer1']}x{r['rozmer2']}x{r['rozmer3']} | Cena: {r['cena']}€/bm"
        vhodne_moznosti.append({"label": label, "cena": float(r['cena'])})
    zoznam_na_vyber = [item['label'] for item in vhodne_moznosti] + ["+ Pridať nový/iný polotovar"]

with col_m3:
    idx_start = len(zoznam_na_vyber)-1 if akost_vyber == "+ Iná akosť (zadať manuálne)" else 0
    vybrany_polo_str = st.selectbox("Výber polotovaru (zoznam)", zoznam_na_vyber, index=idx_start, key="polo_inteligent")

# --- LOGIKA PRIRADENIA CENY ---
cena_polotovaru = 0.0
if vybrany_polo_str == "+ Pridať nový/iný polotovar":
    st.warning("ℹ️ Zadajte parametre pre nový polotovar nižšie")
    c_n1, c_n2, c_n3, c_n4, c_n5, c_n6 = st.columns(6)
    with c_n1:
        povodna = "" if akost_vyber == "+ Iná akosť (zadať manuálne)" else akost_vyber
        nova_akost = st.text_input("Názov akosti", value=povodna)
    with c_n2: nova_cena = st.number_input("Cena (€/bm)", min_value=0.0, format="%.2f")
    # ... r1, r2, r3 ostanú ako si ich mala ...
    cena_polotovaru = nova_cena
else:
    vybrany_objekt = next((item for item in vhodne_moznosti if item['label'] == vybrany_polo_str), None)
    if vybrany_objekt: 
        cena_polotovaru = vybrany_objekt['cena']

# --- VÝPOČET A ZOBRAZENIE CIEN VEDĽA VÝBERU ---
dlzka_pre_vypocet = l if tvar_item == "KR" else v
cena_mat_kus = (dlzka_pre_vypocet / 1000) * cena_polotovaru

with col_m4:
    st.metric(label="Cena za bm", value=f"{cena_polotovaru:.2f} €")
with col_m5:
    st.metric(label="Mat. / kus", value=f"{cena_mat_kus:.3f} €")

# --- 7. SEKCIU: INTERNÁ KLASIFIKÁCIA MECASYS (SUBCATEGORY A HUSTOTA) ---

import re

# 1. PRÍPRAVA VSTUPNEJ AKOSTI (Čistenie a ošetrenie)
# Zisťujeme, či užívateľ vybral akosť zo zoznamu alebo zadal vlastnú
if akost_vyber == "+ Iná akosť (zadať manuálne)":
    # Prevedieme na veľké písmená, odstránime všetky medzery a biele znaky
    relevantna_akost = nova_akost.upper().replace(" ", "").strip()
else:
    relevantna_akost = akost_vyber.upper().replace(" ", "").strip()

def get_mecasys_logic(material_vstup, akost_str):
    """
    Logika podľa dokumentov:
    - SUBCATEGORY_revB.docx (Klasifikácia a výnimky)
    - HUSTOTA_definicia.docx (Priradenie hustoty v kg/m3)
    """
    sub = "OSTATNÉ"
    rho = 0.0  # Hustota v kg/m3
    
    if not akost_str:
        return sub, rho

    # Extrakcia čísla WNr (napr. z "1.2379" vytiahne 1.2379 pre porovnávanie rozsahov)
    match = re.search(r"\d\.\d{4}", akost_str)
    wnr_val = float(match.group()) if match else 0.0

    # --- A. CATEGORY: OCEĽ ---
    if material_vstup == "OCEĽ":
        rho = 7900.0  # Fixná hustota pre všetky ocele
        
        # 1. Výnimky (majú prednosť)
        if akost_str.startswith("1.3505") or akost_str.startswith("1.35"):
            sub = "TOOL"
        elif any(akost_str.startswith(x) for x in ["1.0619", "1.07", "1.11", "1.12"]):
            sub = "UNALL"
        elif akost_str.startswith("1.39"):
            sub = "ALLOYED"
        elif akost_str.startswith("1.29"):
            sub = "TOOL"
        # 2. Rozsahy DIN
        elif 1.0000 <= wnr_val <= 1.1499: sub = "UNALL"
        elif 1.1500 <= wnr_val <= 1.6499: sub = "LOWAL"
        elif 1.6500 <= wnr_val <= 1.8999: sub = "ALLOYED"
        elif (1.2000 <= wnr_val <= 1.3299) or (1.3500 <= wnr_val <= 1.3599): sub = "TOOL"
        elif 1.3300 <= wnr_val <= 1.3899: sub = "HSS"

    # --- B. CATEGORY: NEREZ ---
    elif material_vstup == "NEREZ":
        rho = 8000.0  # Fixná hustota pre všetky nereze
        
        # 1. Výnimky (majú prednosť)
        if akost_str.startswith("1.47") or akost_str.startswith("1.48"):
            sub = "STAIN-SPEC"
        elif akost_str.startswith("1.4308") or akost_str.startswith("1.4408"):
            sub = "AUST"
        elif akost_str.startswith("1.4462"):
            sub = "DUPX"
        # 2. Rozsahy DIN
        elif 1.4300 <= wnr_val <= 1.4599: sub = "AUST"
        elif akost_str.startswith("1.41"): sub = "MART"
        elif akost_str.startswith("1.44"): sub = "DUPX"
        elif akost_str.startswith("1.40"): sub = "FERR"
        elif 1.4600 <= wnr_val <= 1.4999: sub = "STAIN-SPEC"

    # --- C. CATEGORY: FAREBNÉ KOVY ---
    elif material_vstup == "FAREBNÉ KOVY":
        # Subcategory a hustota podľa DIN rozsahov z HUSTOTA_definicia
        if 2.0000 <= wnr_val <= 2.0199: sub, rho = "CU", 9000.0
        elif 2.0200 <= wnr_val <= 2.0599: sub, rho = "BRASS", 9000.0
        elif 2.0900 <= wnr_val <= 2.1399: sub, rho = "BRONZE", 9000.0
        elif 3.0000 <= wnr_val <= 3.5999: sub, rho = "ALU", 2900.0
        elif akost_str.startswith("3.7"): sub, rho = "TI", 4500.0
        elif akost_str.startswith("2.4"): sub, rho = "NI-SPEC", 8500.0

    # --- D. CATEGORY: PLAST ---
    elif material_vstup == "PLAST":
        # Vyhľadávanie kľúčových slov v názve akosti
        if "POM" in akost_str: sub, rho = "POM", 1500.0
        elif any(x in akost_str for x in ["PE", "HDPE"]): sub, rho = "PE", 1000.0
        elif "PA" in akost_str: sub, rho = "PA", 1200.0
        elif "PP" in akost_str: sub, rho = "PP", 1000.0
        elif "PEEK" in akost_str: sub, rho = "PEEK", 1400.0
        elif "PET" in akost_str: sub, rho = "PET", 1700.0
        elif "PC" in akost_str or "LEXAN" in akost_str: sub, rho = "PC", 1500.0
        elif "PVC" in akost_str: sub, rho = "PVC", 1700.0
        elif "PTFE" in akost_str or "TEFLON" in akost_str: sub, rho = "PTFE", 3000.0
        elif "PUR" in akost_str: sub, rho = "PUR", 2000.0
        elif any(x in akost_str for x in ["RUBBER", "GUMA"]): sub, rho = "RUBBER", 1200.0
        else: sub, rho = "OSTATNÉ", 1400.0

    # --- E. CATEGORY: LIATINA ---
    elif material_vstup == "LIATINA":
        if akost_str.startswith("0.60"): sub, rho = "CAST-GG", 7150.0
        elif akost_str.startswith("0.70"): sub, rho = "CAST-GGG", 7250.0
        elif 0.8000 <= wnr_val <= 0.9699: sub, rho = "CAST-TEMP", 7400.0

    return sub, rho

# 2. FINÁLNE PRIRADENIE PREMENNÝCH
subcategory, hustota = get_mecasys_logic(material_vyber, relevantna_akost)

# 3. KONTROLNÝ VÝPIS PRE PROGRAMÁTORA (Skrytý alebo v expaderi)
# Tento výpis slúži len na overenie, že premenné sú správne naplnené
st.write(f"DEBUG: Subcategory={subcategory}, Hustota={hustota} kg/m3")
