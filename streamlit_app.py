import streamlit as st
import pandas as pd
import requests
import datetime
import re
import math

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

# --- NAČÍTANIE DÁT ---
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSuHQWbpryWNerWr8aKKheHbzTPhXI6lS7YH1sL5zwFIIzLfpTZz47acY_ua2e_fVqEcfxMBe5wnjue/pub?gid=0&single=true&output=csv"
df = pd.read_csv(sheet_url)

material_sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQf4EiqZt1grkazJgfYWVhG0M8FGLNCjaGk6dcXhO3r04JQuZ9Qxv1jelDo3c8hBLy7Ny5C1pZqvbfS/pub?output=csv"
df_mat = pd.read_csv(material_sheet_url)

# Cenník kooperácií
sheet_koop_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRfPBZ4TCpQyiqybU0ADu3AMwHCi2qOKifQAOnnTWnorVNJ1SVxtN6zJzXthOxCVwtXWp__Bp_-nto0/pub?gid=1180392224&single=true&output=csv"
@st.cache_data
def load_koop_data(url):
    data = pd.read_csv(url)
    data.columns = data.columns.str.strip()
    return data
df_koop = load_koop_data(sheet_koop_url)

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
    with col3: zakaznik = st.text_input("Zadajte meno nového zákazníka", key="new_cust_name")
    with col4:
        krajina_hodnota = st.text_input("Krajina Zákazníka (manuálne)", key="new_cust_country")
        lojalita = 0.5
else:
    data_zakaznika = df[df['zakaznik'] == vyber].iloc[0]
    zakaznik = vyber
    krajina_hodnota = str(data_zakaznika['krajina'])
    lojalita = float(data_zakaznika['lojalita'])
    with col4: st.text_input("Krajina Zákazníka", value=krajina_hodnota, disabled=True)

st.divider()
# --- 5. RIADOK: POLOŽKA (ITEM) S LOGIKOU RESETU ---

# Inicializácia session_state pre držanie hodnôt, ak ešte neexistujú
if "stary_item" not in st.session_state:
    st.session_state.stary_item = ""
if "pocet_kusov" not in st.session_state:
    st.session_state.pocet_kusov = 1
if "narocnost" not in st.session_state:
    st.session_state.narocnost = 1
if "tvar_item" not in st.session_state:
    st.session_state.tvar_item = "STV"
if "d_rozmer" not in st.session_state:
    st.session_state.d_rozmer = 0.0
if "l_rozmer" not in st.session_state:
    st.session_state.l_rozmer = 0.0
if "s_rozmer" not in st.session_state:
    st.session_state.s_rozmer = 0.0
if "v_rozmer" not in st.session_state:
    st.session_state.v_rozmer = 0.0

col5, col6, col7, col8, col9, col10, col11, col12 = st.columns(8)

with col5:
    # Textový vstup pre ITEM
    aktualny_item = st.text_input("ITEM", value=st.session_state.stary_item, key="item_input")

# --- KLÚČOVÁ LOGIKA PREMAZÁVANIA ---
# Ak používateľ zmenil ITEM (a nie je prázdny), resetujeme ostatné polia v session_state
if aktualny_item != st.session_state.stary_item:
    st.session_state.stary_item = aktualny_item
    st.session_state.pocet_kusov = 1
    st.session_state.narocnost = 1
    st.session_state.tvar_item = "STV"
    st.session_state.d_rozmer = 0.0
    st.session_state.l_rozmer = 0.0
    st.session_state.s_rozmer = 0.0
    st.session_state.v_rozmer = 0.0
    # Rýchly reštart skriptu, aby sa hneď aplikovali vymazané hodnoty do vizuálnych prvkov
    st.rerun()

# --- Vykreslenie prvkov s naviazaním na session_state ---
with col6:
    pocet_kusov = st.number_input("Počet kusov", min_value=1, value=st.session_state.pocet_kusov, key="pocet_input")
    st.session_state.pocet_kusov = pocet_kusov

with col7:
    # Nájdeme index aktuálnej náročnosti, aby selectbox správne zobrazil predvolenú hodnotu
    moznosti_narocnosti = [1, 2, 3, 4, 5]
    idx_narocnost = moznosti_narocnosti.index(st.session_state.narocnost)
    narocnost = st.selectbox("Náročnosť", options=moznosti_narocnosti, index=idx_narocnost, key="narocnost_input")
    st.session_state.narocnost = narocnost

with col8:
    moznosti_tvarov = ["STV", "KR"]
    idx_tvar = moznosti_tvarov.index(st.session_state.tvar_item)
    tvar_item = st.selectbox("Tvar položky", options=moznosti_tvarov, index=idx_tvar, key="tvar_input")
    st.session_state.tvar_item = tvar_item

# Dynamické rozmery podľa tvaru
if tvar_item == "KR":
    with col9:
        d = st.number_input("D(mm)", min_value=0.0, format="%.1f", value=st.session_state.d_rozmer, key="d_kr")
        st.session_state.d_rozmer = d
    with col10:
        l = st.number_input("L(mm)", min_value=0.0, format="%.1f", value=st.session_state.l_rozmer, key="l_kr")
        st.session_state.l_rozmer = l
    s, v = 0.0, 0.0
else:
    with col9:
        d = st.number_input("D/P(mm)", min_value=0.0, format="%.1f", value=st.session_state.d_rozmer, key="d_stv")
        st.session_state.d_rozmer = d
    with col10:
        s = st.number_input("S(mm)", min_value=0.0, format="%.1f", value=st.session_state.s_rozmer, key="s_stv")
        st.session_state.s_rozmer = s
    with col11:
        v = st.number_input("V(mm)", min_value=0.0, format="%.1f", value=st.session_state.v_rozmer, key="v_stv")
        st.session_state.v_rozmer = v
    l = 0.0

st.divider()

# --- 6. RIADOK: MATERIÁL A POLOTOVAR ---
df_mat.columns = [c.lower().strip() for c in df_mat.columns]
def get_sorted_dims(a, b, c):
    try: return sorted([float(a), float(b), float(c)], reverse=True)
    except: return [0.0, 0.0, 0.0]

col_m1, col_m2, col_m3 = st.columns([2, 3, 3])

with col_m1:
    zoznam_materialov = sorted(df_mat['material'].unique())
    material_vyber = st.selectbox("Materiál", zoznam_materialov, key="mat_select")

with col_m2:
    filtr_akosti_vsetky = sorted(df_mat[df_mat['material'] == material_vyber]['akost'].unique().astype(str))
    akost_vyber_list = st.multiselect("Výber akostí", options=filtr_akosti_vsetky, key="akost_multi")
    manual_akost_check = st.checkbox("+ Iná akosť (manuálne)")

vhodne_moznosti = []
if manual_akost_check:
    zoznam_na_vyber = ["+ Pridať nový/iný polotovar"]
else:
    df_relevant = df_mat[(df_mat['material'] == material_vyber) & (df_mat['akost'].astype(str).isin(akost_vyber_list))].copy()
    
    if tvar_item == "KR":
        mask = df_relevant['názov'].str.contains('KR|6HR|TR', case=False, na=False)
        df_relevant = df_relevant[mask]
    else:
        pass

    if not df_relevant.empty:
        df_relevant['sort_key'] = df_relevant.apply(lambda r: get_sorted_dims(r['rozmer1'], r['rozmer2'], r['rozmer3']), axis=1)
        df_relevant = df_relevant.sort_values(by='sort_key')
        for idx, r in df_relevant.iterrows():
            label = f"[{r['akost']}] {r['názov']} | {r['rozmer1']}x{r['rozmer2']}x{r['rozmer3']} | Cena: {r['cena']}€/bm"
            vhodne_moznosti.append({"label": label, "cena": float(r['cena']), "akost_povodna": str(r['akost'])})
    zoznam_na_vyber = [item['label'] for item in vhodne_moznosti] + ["+ Pridať nový/iný polotovar"]

with col_m3:
    idx_start = len(zoznam_na_vyber)-1 if manual_akost_check else 0
    vybrany_polo_str = st.selectbox("Výber polotovaru (zoznam)", zoznam_na_vyber, index=idx_start, key="polo_inteligent")

cena_polotovaru = 0.0
relevantna_akost = ""

if vybrany_polo_str == "+ Pridať nový/iný polotovar":
    c_n1, c_n2, c_n3, c_n4, c_n5, c_n6 = st.columns(6)
    with c_n1:
        povodna_akost_val = akost_vyber_list[0] if akost_vyber_list else ""
        nova_akost = st.text_input("Názov akosti", value="" if manual_akost_check else povodna_akost_val)
    with c_n2: nova_cena = st.number_input("Cena (€/bm)", min_value=0.0, format="%.2f")
    with c_n3: r1 = st.number_input("Rozmer 1", min_value=0.0)
    with c_n4: r2 = st.number_input("Rozmer 2", min_value=0.0)
    with c_n5: r3 = st.number_input("Rozmer 3", min_value=0.0)
    with c_n6: nazov_pol = st.text_input("Názov polotovaru", value="MANUAL")
    cena_polotovaru = nova_cena
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
        # 1. Najšpecifickejšie (PEEK, PET-G, PMMA)
        if "PEEK" in akost_str: 
            sub, rho = "PEEK", 1400.0
        elif "PET-G" in akost_str or "PETG" in akost_str:
            sub, rho = "PET-G", 1270.0
        elif "PMMA" in akost_str or "PLEXI" in akost_str or "AKRYLAT" in akost_str:
            sub, rho = "PMMA", 1200.0
            
        # 2. Skupiny s viacerými názvami
        elif "PC" in akost_str or "LEXAN" in akost_str:
            sub, rho = "PC", 1200.0
        elif "PUR" in akost_str or "EBABOARD" in akost_str or "EBABLOCK" in akost_str:
            sub, rho = "PUR", 1200.0 # hustota podľa typu polyuretánu
        elif "EPDM" in akost_str or "GUMA" in akost_str or "RUBBER" in akost_str:
            sub, rho = "RUBBER", 1150.0
        elif "PVC" in akost_str:
            sub, rho = "PVC", 1400.0
            
        # 3. Štandardné plasty
        elif "POM" in akost_str:
            sub, rho = "POM", 1500.0
        elif "PET" in akost_str: # PET zachytí zvyšné PET (nie PET-G)
            sub, rho = "PET", 1700.0
        elif "PA" in akost_str:
            sub, rho = "PA", 1200.0
        elif "PP" in akost_str:
            sub, rho = "PP", 1000.0
            
        # 4. Posledný musí byť PE (kvôli PEEK)
        elif "PE" in akost_str or "HDPE" in akost_str:
            sub, rho = "PE", 1000.0
  
    elif cat == "LIATINA":
        if "0.60" in akost_str: sub, rho = "CAST-GG", 7150.0
        elif "0.70" in akost_str: sub, rho = "CAST-GGG", 7250.0
        elif 0.8000 <= wnr_val <= 0.9699: sub, rho = "CAST-TEMP", 7400.0
    return sub, rho

subcategory, hustota_auto = get_mecasys_logic(material_vyber, relevantna_akost)
hustota = hustota_auto
if hustota_auto == 0.0:
    hustota = st.number_input("Manuálna hustota (kg/m³)", min_value=0.0, key="manual_rho")

# --- 8. VÝPOČET GEOMETRIE A PRÍPRAVA PRE RF MODELY ---
kr1_predikovany = 0.0   # Predikovaný výrobný čas (KR)
kr2_predikovany = 0.0   # Predikovaná cena komponentu (KR)
stv1_predikovany = 0.0  # Predikovaný výrobný čas (STV)
stv2_predikovany = 0.0  # Predikovaná cena komponentu (STV)

if tvar_item == "KR":
    plocha_prierezu = (math.pi * (d**2)) / 4
    povrch_celkovy_mm2 = (2 * plocha_prierezu) + (math.pi * d * l) # Opravil som '1' na 'l' z tvojho pôvodného kódu, ak tam patrí dĺžka
    hmotnost_kusu = (plocha_prierezu * l * hustota) / 1e9          # Opravil som '1' na 'l' z tvojho pôvodného kódu
    
    # 🔮 TU DNES ZAPOJÍŠ SVOJE RF MODELY PRE KR:
    # kr1_predikovany = float(model_rf_kr_cas.predict(...)[0])
    # kr2_predikovany = float(model_rf_kr_cena.predict(...)[0])
    
    # Pre testovacie účely tam môžeš hodiť fixné čísla, napr:
    kr1_predikovany = 12.5
    kr2_predikovany = 35.0

else:
    plocha_prierezu = s * v
    povrch_celkovy_mm2 = 2 * (s * v + s * d + v * d)
    hmotnost_kusu = (s * v * d * hustota) / 1e9
    
    # 🔮 TU DNES ZAPOJÍŠ SVOJE RF MODELY PRE STV:
    # stv1_predikovany = float(model_rf_stv_cas.predict(...)[0])
    # stv2_predikovany = float(model_rf_stv_cena.predict(...)[0])
    
    # Pre testovacie účely:
    stv1_predikovany = 22.0
    stv2_predikovany = 65.0

plocha_prierez_dm2 = povrch_celkovy_mm2 / 10000 
hmotnost_celkom = hmotnost_kusu * pocet_kusov
# --- 9. KOOPERÁCIA A FINÁLNE CENY (AKTUALIZOVANÁ LOGIKA FILTROVANIA) ---
st.write("---")
rk1, rk2, rk3, rk4, rk5, rk6, rk7 = st.columns([0.8, 1.5, 1.5, 1.2, 1.2, 1.2, 1.5])

with rk1:
    je_kooperacia = st.checkbox("Koop?", value=False)

cena_kooperacia = 0.0
if je_kooperacia:
    with rk3:
        # 1. Získame unikátne materiály z cenníka kooperácií
        zoznam_vsetkych_mat_koop = sorted(df_koop['material'].unique())
        
        # 2. Skúsime nájsť index materiálu, ktorý bol vybraný hore v sekcii Komponent
        try:
            default_idx = zoznam_vsetkych_mat_koop.index(material_vyber)
        except ValueError:
            default_idx = 0 # Ak sa nenašiel, dáme prvý v zozname
            
        vybrany_mat_koop = st.selectbox("Mat. koop.", zoznam_vsetkych_mat_koop, index=default_idx, key="mat_k")
    
    with rk2:
        # 3. Vyfiltrujeme operácie (druh) len pre tento konkrétny vybraný materiál koop
        mozne_operacie = sorted(df_koop[df_koop['material'] == vybrany_mat_koop]['druh'].unique())
        vybrany_druh = st.selectbox("Druh koop.", mozne_operacie, key="druh_k")
    
    # Doťahovanie údajov z riadku
    riadok_koop = df_koop[(df_koop['druh'] == vybrany_druh) & (df_koop['material'] == vybrany_mat_koop)].iloc[0]
    tarifa = float(riadok_koop['tarifa'])
    jednotka = str(riadok_koop['jednotka']).strip().lower()
    min_obj = float(riadok_koop['minimum'])

    vyp_cena = tarifa * (hmotnost_kusu if jednotka == "kg" else plocha_prierez_dm2 if jednotka == "dm2" else 1)
    cena_kooperacia = max(vyp_cena, min_obj / pocet_kusov)
else:
    with rk2: st.text_input("Druh koop.", "-", disabled=True)
    with rk3: st.text_input("Mat. koop.", "-", disabled=True)

vstupne_naklady = cena_mat_kus + cena_kooperacia

# Zobrazenie cien a nákladov v metrikách
with rk4: st.metric("Cena/bm", f"{cena_polotovaru:.2f} €")
with rk5: st.metric("Mat./kus", f"{cena_mat_kus:.3f} €")
with rk6: st.metric("Koop./kus", f"{cena_kooperacia:.3f} €")
with rk7: st.metric("VSTUPNÉ NÁKLADY", f"{vstupne_naklady:.3f} €", delta=f"{hmotnost_kusu:.2f} kg", delta_color="off")

# --- NOVÝ SPODNÝ INFORMAČNÝ PANEL S EDITÁCIOU PREDIKCIÍ ---

# --- NOVÝ SPODNÝ INFORMAČNÝ PANEL S EDITÁCIOU PREDIKCIÍ (VEDĽA SEBA) ---
st.write("")
# Vytvoríme sivý box pomocou HTML/CSS kontajneru v Streamlite
with st.container():
    st.markdown(
        """
        <style>
        .sivy-panel {
            background-color: #f1f3f6;
            padding: 15px;
            border-radius: 5px;
            font-size: 0.9em;
            color: #333;
            border-left: 5px solid #bdc3c7;
        }
        </style>
        """, unsafe_allow_html=True
    )
    
    # Spustíme div pre sivé pozadie
    st.markdown('<div class="sivy-panel">', unsafe_allow_html=True)
    
    # Rozdelíme panel na dve hlavné časti: vľavo technické info, vpravo predikcie
    col_inf1, col_inf2 = st.columns([4, 4])
    
    with col_inf1:
        st.markdown(f"""
        <strong>Použitá akosť:</strong> {relevantna_akost} &nbsp;|&nbsp; 
        <strong>Subcategory:</strong> {subcategory} &nbsp;|&nbsp; 
        <strong>Hustota:</strong> {hustota:.0f} kg/m³ <br>
        <strong>Plocha prierezu:</strong> {plocha_prierezu:.2f} mm² &nbsp;|&nbsp; 
        <strong>Hmotnosť:</strong> {hmotnost_kusu:.3f} kg &nbsp;|&nbsp; 
        <strong>Povrch:</strong> {plocha_prierez_dm2:.3f} dm²
        """, unsafe_allow_html=True)
        
    with col_inf2:
        # Vytvoríme dva pod-stĺpce vedľa seba pre editovateľné polia
        col_cas, col_cena = st.columns(2)
        
        # Podľa zvoleného tvaru podhodíme užívateľovi hodnoty z RF modelov
        if tvar_item == "KR":
            with col_cas:
                finalny_cas = st.number_input("Schváliť výrobný čas (min)", min_value=0.0, value=kr1_predikovany, format="%.2f", key="schvaleny_cas_kr")
            with col_cena:
                finalna_cena = st.number_input("Schváliť cenu komponentu (€)", min_value=0.0, value=kr2_predikovany, format="%.2f", key="schvalena_cena_kr")
        else:
            with col_cas:
                finalny_cas = st.number_input("Schváliť výrobný čas (min)", min_value=0.0, value=stv1_predikovany, format="%.2f", key="schvaleny_cas_stv")
            with col_cena:
                finalna_cena = st.number_input("Schváliť cenu komponentu (€)", min_value=0.0, value=stv2_predikovany, format="%.2f", key="schvalena_cena_stv")

    st.markdown('</div>', unsafe_allow_html=True)
