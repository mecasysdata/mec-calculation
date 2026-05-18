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
if "cena_potvrdena" not in st.session_state:
    st.session_state.cena_potvrdena = False
if "schvalena_cena" not in st.session_state:
    st.session_state.schvalena_cena = 3.0

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
        kluce_na_vymazanie = ["pocet_input", "narocnost_input", "tvar_input", "d_kr", "l_kr", "d_stv", "s_stv", "v_stv", "mat_select", "akost_multi", "man_akost_chk", "polo_inteligent", "koop_main_checkbox", "manual_rho", "mat_k", "druh_k", "vystupny_cas_input", "vystupna_cena_input"]
        for klic in kluce_na_vymazanie:
            if klic in st.session_state:
                del st.session_state[klic]
        
        # Reset stavov pre AI model
        st.session_state.cas_potvrdeny = False
        st.session_state.schvaleny_cas = 3.0
        st.session_state.cena_potvrdena = False
        st.session_state.schvalena_cena = 3.0
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
    match = re.search(r"\d\.\d{2,4}", akost_str)
    wnr_val = round(float(match.group()), 4) if match else 0.0
    
    if cat == "OCEĽ":
        rho = 7900.0
        if any(x in akost_str for x in ["1.3505", "1.35"]): sub = "TOOL"
        elif any(x in akost_str for x in ["1.0619", "1.07", "1.11", "1.12"]): sub = "UNALL"
        elif "1.39" in akost_str: sub = "ALLOYED"
        elif "1.29" in akost_str: sub = "TOOL"
        elif 1.0000 <= wnr_val <= 1.1499: sub = "UNALL"
        elif 1.1500 <= wnr_val <= 1.6499: sub = "LOWAL"
        elif 1.6500 <= wnr_val <= 1.8999: sub = "ALLOYED"
        elif (1.2000 <= wnr_val <= 1.3299) or (1.3500 <= wnr_val <= 1.3599): sub = "TOOL"
        elif 1.3300 <= wnr_val <= 1.3899: sub = "HSS"
    elif cat == "NEREZ":
        rho = 8000.0
        if any(x in akost_str for x in ["1.47", "1.48"]): sub = "STAIN-SPEC"
        elif any(x in akost_str for x in ["1.4308", "1.4408"]): sub = "AUST"
        elif "1.4462" in akost_str: sub = "DUPX"
        elif 1.4300 <= wnr_val <= 1.4599: sub = "AUST"
        elif "1.41" in akost_str: sub = "MART"
        elif "1.44" in akost_str: sub = "DUPX"
        elif "1.40" in akost_str: sub = "FERR"
        elif 1.4600 <= wnr_val <= 1.4999: sub = "STAIN-SPEC"
    elif cat == "FAREBNÉ KOVY":
        if 2.0000 <= wnr_val <= 2.0199: sub, rho = "CU", 9000.0
        elif 2.0200 <= wnr_val <= 2.0899: sub, rho = "BRASS", 9000.0
        elif 2.0900 <= wnr_val <= 2.3999: sub, rho = "BRONZE", 9000.0
        elif 3.0000 <= wnr_val <= 3.5999: sub, rho = "ALU", 2900.0
        elif "3.7" in akost_str: sub, rho = "TI", 4500.0
        elif "2.4" in akost_str: sub, rho = "NI-SPEC", 8500.0
    elif cat == "PLAST":
        if "PEEK" in akost_str: sub, rho = "PEEK", 1400.0
        elif "PET-G" in akost_str or "PETG" in akost_str: sub, rho = "PET-G", 1270.0
        elif "PMMA" in akost_str or "PLEXI" in akost_str or "AKRYLAT" in akost_str: sub, rho = "PMMA", 1200.0
        elif "PC" in akost_str or "LEXAN" in akost_str: sub, rho = "PC", 1200.0
        elif "PUR" in akost_str or "EBABOARD" in akost_str or "EBABLOCK" in akost_str: sub, rho = "PUR", 1200.0
        elif "EPDM" in akost_str or "GUMA" in akost_str or "RUBBER" in akost_str: sub, rho = "RUBBER", 1150.0
        elif "PVC" in akost_str: sub, rho = "PVC", 1400.0
        elif "POM" in akost_str: sub, rho = "POM", 1500.0
        elif "PET" in akost_str: sub, rho = "PET", 1700.0
        elif "PA" in akost_str: sub, rho = "PA", 1200.0
        elif "PP" in akost_str: sub, rho = "PP", 1000.0
        elif "PE" in akost_str or "HDPE" in akost_str: sub, rho = "PE", 1000.0
    elif cat == "LIATINA":
        if "0.60" in akost_str: sub, rho = "CAST-GG", 7150.0
        elif "0.70" in akost_str: sub, rho = "CAST-GGG", 7250.0
        elif 0.8000 <= wnr_val <= 0.9699: sub, rho = "CAST-TEMP", 7400.0
    return sub, rho

subcategory, hustota_auto = get_mecasys_logic(material_vyber, relevantna_akost)
hustota = hustota_auto
if hustota_auto == 0.0:
    with col_m1:
        hustota = st.number_input("Manuálna hustota (kg/m³)", min_value=0.0, value=7850.0, key="manual_rho")

# --- 8. VÝPOČET GEOMETRIE ---
if tvar_item == "KR":
    plocha_prierezu = (math.pi * (d**2)) / 4
    povrch_celkovy_mm2 = (2 * plocha_prierezu) + (math.pi * d * l)
    hmotnost_kusu = (plocha_prierezu * l * hustota) / 1e9
else:
    plocha_prierezu = s * v
    povrch_celkovy_mm2 = 2 * (s * v + s * d + v * d)
    hmotnost_kusu = (s * v * d * hustota) / 1e9

plocha_prierez_dm2 = povrch_celkovy_mm2 / 10000 
hmotnost_celkom = hmotnost_kusu * pocet_kusov

# --- 9. KOOPERÁCIA A FINÁLNE CENY ---
st.write("---")
rk1, rk2, rk3, rk4, rk5, rk6, rk7 = st.columns([0.8, 1.5, 1.5, 1.2, 1.2, 1.2, 1.5])

with rk1:
    je_kooperacia = st.checkbox("Koop?", value=False, key="koop_main_checkbox")

cena_kooperacia = 0.0

if je_kooperacia:
    zoznam_vsetkych_mat_koop = sorted(df_koop['material'].dropna().unique()) if 'material' in df_koop.columns else []
    
    try: default_idx = zoznam_vsetkych_mat_koop.index(material_vyber)
    except ValueError: default_idx = 0
        
    with rk3:
        vybrany_mat_koop = st.selectbox("Mat. koop.", zoznam_vsetkych_mat_koop, index=default_idx, key="mat_k")
    
    with rk2:
        df_f_koop = df_koop[df_koop['material'] == vybrany_mat_koop]
        mozne_operacie = sorted(df_f_koop['druh'].dropna().unique()) if 'druh' in df_f_koop.columns else []
        vybrany_druh = st.selectbox("Druh koop.", mozne_operacie, key="druh_k")
    
    filter_koop_row = df_koop[(df_koop['druh'] == vybrany_druh) & (df_koop['material'] == vybrany_mat_koop)]
    
    if not filter_koop_row.empty:
        riadok_koop = filter_koop_row.iloc[0]
        tarifa = float(riadok_koop.get('tarifa', 0))
        jednotka = str(riadok_koop.get('jednotka', '')).strip().lower()
        min_obj = float(riadok_koop.get('minimum', 0))

        vyp_cena = tarifa * (hmotnost_kusu if jednotka == "kg" else plocha_prierez_dm2 if jednotka == "dm2" else 1)
        cena_kooperacia = max(vyp_cena, min_obj / pocet_kusov)
    else:
        st.warning("Pre zvolenú kombináciu druhu a materiálu kooperácie neboli nájdené ceny.")
else:
    with rk2: st.text_input("Druh koop.", "-", disabled=True, key="disabled_druh_koop")
    with rk3: st.text_input("Mat. koop.", "-", disabled=True, key="disabled_mat_koop")

vstupne_naklady = cena_mat_kus + cena_kooperacia

# Zobrazenie cien a nákladov v metrikách
with rk4: st.metric("Cena/bm", f"{cena_polotovaru:.2f} €")
with rk5: st.metric("Mat./kus", f"{cena_mat_kus:.3f} €")
with rk6: st.metric("Koop./kus", f"{cena_kooperacia:.3f} €")
with rk7: st.metric("VSTUPNÉ NÁKLADY", f"{vstupne_naklady:.3f} €", delta=f"{hmotnost_kusu:.2f} kg", delta_color="off")

# --- SPODNÝ INFORMAČNÝ PANEL (GEOMETRIA) ---
st.markdown(
    f"""
    <div style="background-color: #f1f3f6; padding: 10px; border-radius: 5px; font-size: 0.85em; color: #555;">
    <strong>Použitá akosť:</strong> {relevantna_akost} | <strong>Subcategory:</strong> {subcategory} | <strong>Hustota:</strong> {hustota:.0f} kg/m³ | 
    <strong>Plocha prierezu:</strong> {plocha_prierezu:.2f} mm² | <strong>Hmotnosť:</strong> {hmotnost_kusu:.3f} kg | <strong>Povrch:</strong> {plocha_prierez_dm2:.3f} dm²
    </div>
    """, unsafe_allow_html=True
)

# --- 10. MEC AI COMPACT DASHBOARD (Všetko v jednom riadku podľa dohody) ---
# --- 10. MEC AI COMPACT DASHBOARD ---
st.divider()
st.subheader("🤖MEC AI")

# Definícia fixných zástupných hodnôt podľa typu položky
if tvar_item == "KR":
    model_predikcia_cas = 3.0   
    model_predikcia_cena = 3.0  
else:
    model_predikcia_cas = 3.0   
    model_predikcia_cena = 3.0  

# Vytvorenie 5 stĺpcov vedľa seba v jednom riadku
ai_col1, ai_col2, ai_col3, ai_col4, ai_col5 = st.columns(5)

# --- 1. STĹPEC: Predpokladaný výrobný čas /ks [min] ---
with ai_col1:
    vystupny_cas = st.number_input(
        "Výrobný čas /ks [min]", 
        min_value=0.0, 
        value=float(model_predikcia_cas),
        format="%.2f",
        key="vystupny_cas_input"
    )

# --- 2. STĹPEC: Tlačítko Schváliť výrobný čas ---
with ai_col2:
    st.write("")  
    if st.button("✅ Schváliť výrobný čas", type="secondary", use_container_width=True):
        st.session_state.schvaleny_cas = vystupny_cas
        st.session_state.cas_potvrdeny = True
        st.rerun()

# --- 3. STĹPEC: Predikovaná cena ks ---
with ai_col3:
    if st.session_state.cas_potvrdeny:
        vystupna_cena = st.number_input(
            "Predikovaná cena /ks (€)", 
            min_value=0.0, 
            value=float(model_predikcia_cena),
            format="%.2f",
            key="vystupna_cena_input"
        )
    else:
        st.info("💡 Čaká sa na schválenie času...")
        vystupna_cena = 0.0

# --- 4. STĹPEC: Tlačítko Schváliť cenu ---
with ai_col4:
    st.write("")  
    if st.button("✅ Schváliť cenu", type="secondary", use_container_width=True, disabled=not st.session_state.cas_potvrdeny):
        st.session_state.schvalena_cena = vystupna_cena
        st.session_state.cena_potvrdena = True
        st.rerun()

# --- 5. STĹPEC: Pridanie položky do košíka (Formátovanie rozmerov) ---
with ai_col5:
    st.write("")  
    if st.button("🛒 Pridať item do košíka", type="primary", use_container_width=True, disabled=not st.session_state.cena_potvrdena):
        if item.strip() == "":
            st.warning("Zadaj názov ITEMu pred pridaním.")
        else:
            # Zostavenie reťazca rozmerov podľa tvaru
            if tvar_item == "KR":
                rozmery_formatted = f"{d:.1f} x {l:.1f}"
            else:
                rozmery_formatted = f"{d:.1f} x {s:.1f} x {v:.1f}"

            # Vytvorenie záznamu do košíka (Rozmery sú vložené presne za Akosť)
            nova_polozka = {
                "ITEM": item,
                "Počet kusov": pocet_kusov,
                "Materiál": material_vyber,
                "Akosť": relevantna_akost,
                "Rozmery": rozmery_formatted,  # <-- Tvoj nový stĺpec
                "Výrobný čas (min/ks)": round(st.session_state.schvaleny_cas, 2),
                "Model Cena (€/ks)": round(st.session_state.schvalena_cena, 2),
                "Mat. / kus (€)": round(cena_mat_kus, 3),
                "Koop. / kus (€)": round(cena_kooperacia, 3),
                "Vstupné náklady (€/ks)": round(vstupne_naklady, 3),
                "Celkom za položku (€)": round(vstupne_naklady * pocet_kusov, 2)
            }
            st.session_state.kosik.append(nova_polozka)
            st.success(f"Položka '{item}' pridaná!")
            st.rerun()

if st.session_state.cas_potvrdeny and not st.session_state.cena_potvrdena:
    st.info(f"⏱️ Čas schválený na: **{st.session_state.schvaleny_cas:.2f} min**. Pokračujte schválením ceny kusu.")
elif st.session_state.cena_potvrdena:
    st.success(f"💰 Cena úspešne schválená na: **{st.session_state.schvalena_cena:.2f} €**. Položku môžete vložiť do košíka.")

# --- 11. ZOBRAZENIE KOŠÍKA (Na spodku aplikácie) ---
# --- 11. ZOBRAZENIE KOŠÍKA (Na spodku aplikácie) ---
if st.session_state.kosik:
    st.write("---")
    st.subheader(f"📋 Aktuálny zoznam položiek v ponuke (Počet: {len(st.session_state.kosik)})")
    
    df_kosik = pd.DataFrame(st.session_state.kosik)
    st.dataframe(df_kosik, use_container_width=True, hide_index=True)
    
    celkova_suma = df_kosik["Celkom za položku (€)"].sum()
    
    col_sum1, col_sum2 = st.columns([5, 3])
    with col_sum2:
        st.metric("CELKOVÁ CENA PONUKY", f"{celkova_suma:.2f} €")
        
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🗑️ Vymazať celý košík", type="secondary", use_container_width=True):
            st.session_state.kosik = []
            st.rerun()
            
    st.write("") # Drobné odsadene pre tlačidlá
    
    # Rozdelíme spodný riadok na 2 stĺpce pre Uloženie a PDF generovanie vedľa seba
    col_save, col_pdf = st.columns(2)
    
    with col_save:
        if st.button("💾 Uložiť a Uzatvoriť ponuku", type="primary", use_container_width=True):
            if not ponuka.strip():
                st.error("❌ Prosím, zadaj 'Označenie CP' pred uložením ponuky!")
            elif not zakaznik.strip():
                st.error("❌ Prosím, zadaj alebo vyber 'Názov Zákazníka'!")
            else:
                import requests
                
                riadky_na_zapis = []
                for p in st.session_state.kosik:
                    try:
                        diely_rozmerov = [float(x.strip()) for x in p["Rozmery"].split("x")]
                    except:
                        diely_rozmerov = [0.0, 0.0, 0.0]
                    
                    if len(diely_rozmerov) == 2:
                        tvar_zapis = "KR"
                        val_d = diely_rozmerov[0]
                        val_l = diely_rozmerov[1]
                        val_v = 0.0
                    else:
                        tvar_zapis = "STV"
                        val_d = diely_rozmerov[0] if len(diely_rozmerov) > 0 else 0.0
                        val_l = diely_rozmerov[1] if len(diely_rozmerov) > 1 else 0.0
                        val_v = diely_rozmerov[2] if len(diely_rozmerov) > 2 else 0.0

                    novy_riadok_sheet = {
                        "Dátum CP": datum.strftime("%d.%m.%Y") if hasattr(datum, 'strftime') else str(datum),
                        "Číslo CP": ponuka,
                        "Zákazník": zakaznik,
                        "Krajina": krajina_hodnota,
                        "Lojalita": lojalita,
                        "ITEM": p["ITEM"],
                        "Tvar": tvar_zapis,
                        "Materiál": p["Materiál"],
                        "Akosť": p["Akosť"],
                        "Rozmer D / DP": val_d,
                        "Rozmer L / S": val_l,
                        "Rozmer V": val_v,
                        "Hustota": hustota,  
                        "Hmotnosť kusu (kg)": p["Model Cena (€/ks)"] if p["Počet kusov"] == 0 else round((p
