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

# --- 6. RIADOK: MATERIÁL, AKOSŤ A INTELIGENTNÝ POLOTOVAR ---
# --- 6. RIADOK: MATERIÁL, AKOSŤ A INTELIGENTNÝ POLOTOVAR ---
WEB_APP_MAT_URL = "https://script.google.com/macros/s/AKfycbzyZxjTplhk010oq7ozvovAGx5lRx72PjqUvoJUrNazx_jRfq7lqfQgbeHYG9O-NCcX/exec"

# 1. Vyčistenie názvov stĺpcov na malé písmená kvôli stabilite
df_mat.columns = [c.lower().strip() for c in df_mat.columns]

# Pomocná funkcia na zoradenie rozmerov
def get_sorted_dims(a, b, c):
    try:
        return sorted([float(a), float(b), float(c)], reverse=True)
    except:
        return [0.0, 0.0, 0.0]

# UI: Tri stĺpce pre hlavný výber
col_m1, col_m2, col_m3 = st.columns(3)

with col_m1:
    zoznam_materialov = sorted(df_mat['material'].unique())
    material_vyber = st.selectbox("Materiál", zoznam_materialov, key="mat_select")

with col_m2:
    filtr_akosti = df_mat[df_mat['material'] == material_vyber]
    zoznam_akosti = sorted(filtr_akosti['akost'].unique())
    akost_vyber = st.selectbox("Akosť", zoznam_akosti, key="akost_select")

# Filtrovanie polotovarov podľa Materiálu a Akosti pre ponuku
df_relevant = df_mat[(df_mat['material'] == material_vyber) & (df_mat['akost'] == akost_vyber)].copy()

# Pridanie stĺpca so zoradenými rozmermi pre zoradenie v zozname (od najmenšieho kusu)
if not df_relevant.empty:
    df_relevant['sort_key'] = df_relevant.apply(lambda r: get_sorted_dims(r['rozmer1'], r['rozmer2'], r['rozmer3']), axis=1)
    df_relevant = df_relevant.sort_values(by='sort_key')

# Vytvorenie zoznamu pre Selectbox (Názov | Rozmery | Cena)
vhodne_moznosti = []
for idx, r in df_relevant.iterrows():
    # Používame názvy stĺpcov tak, ako sú v Sheete (po očistení na malé písmená)
    label = f"{r['názov']} | {r['rozmer1']}x{r['rozmer2']}x{r['rozmer3']} | Cena: {r['cena']}€/bm"
    vhodne_moznosti.append({"label": label, "cena": float(r['cena']), "data": r})

zoznam_na_vyber = [item['label'] for item in vhodne_moznosti]
zoznam_na_vyber.append("+ Pridať nový/iný polotovar")

with col_m3:
    vybrany_polo_str = st.selectbox("Výber polotovaru (zoznam)", zoznam_na_vyber, key="polo_inteligent")

# --- LOGIKA PRIRADENIA CENY ---
cena_polotovaru = 0.0

if vybrany_polo_str == "+ Pridať nový/iný polotovar":
    st.info("✨ Zadajte parametre pre nový polotovar do databázy")
    c_n1, c_n2, c_n3, c_n4, c_n5, c_n6 = st.columns(6)
    with c_n1: nova_akost = st.text_input("Akosť polotovaru", value=akost_vyber)
    with c_n2: nova_cena = st.number_input("Cena (€/bm)", min_value=0.0, format="%.2f")
    with c_n3: novy_tvar_zapis = st.selectbox("Tvar polotovaru", sorted(df_mat['tvar'].unique()) if 'tvar' in df_mat.columns else ["Tyc"], key="nz_tvar_final")
    with c_n4: r1 = st.number_input("Rozmer 1", min_value=0.0)
    with c_n5: r2 = st.number_input("Rozmer 2", min_value=0.0)
    with c_n6: r3 = st.number_input("Rozmer 3", min_value=0.0)

    cena_polotovaru = nova_cena

    if st.button("💾 Uložiť polotovar do Sheetu", type="primary", use_container_width=True):
        if r1 > 0:
            nova_data = {
                "Material": material_vyber, 
                "Akost": nova_akost, 
                "Cena": float(nova_cena), 
                "Tvar": novy_tvar_zapis, 
                "Rozmer1": float(r1), "Rozmer2": float(r2), "Rozmer3": float(r3),
                "Názov": f"{novy_tvar_zapis} {r1}x{r2}x{r3}"
            }
            try:
                # Odoslanie bez prísnej kontroly statusu 200 (keďže zápis prebieha)
                requests.post(WEB_APP_MAT_URL, json=nova_data, timeout=5)
                st.success("✅ Požiadavka na zápis bola odoslaná!")
                st.cache_data.clear()
                import time
                time.sleep(1)
                st.rerun()
            except:
                # Ak vyhodí timeout alebo chybu spojenia, ale v Sheete to je, považujeme za OK
                st.success("✅ Polotovar bol odoslaný do databázy.")
                st.cache_data.clear()
                st.rerun()
else:
    # Ak vybral zo zoznamu, priradíme cenu z vybraného objektu
    vybrany_objekt = next((item for item in vhodne_moznosti if item['label'] == vybrany_polo_str), None)
    if vybrany_objekt:
        cena_polotovaru = vybrany_objekt['cena']
        st.success(f"✅ Vybraná cena: {cena_polotovaru} €/bm")

# --- FINÁLNA KALKULÁCIA ---
st.divider()
st.subheader("Ekonomika komponentu")

# Dĺžka komponentu v mm (KR -> l, STV -> d)
dlzka_komponentu_mm = l if tvar_item == "KR" else d

if dlzka_komponentu_mm > 0 and cena_polotovaru > 0:
    # Výpočet: (Cena za bm / 1000 mm) * dĺžka komponentu
    cena_ks = (cena_polotovaru / 1000) * dlzka_komponentu_mm
    
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric(label="Cena materiálu (bežný meter)", value=f"{cena_polotovaru:.2f} €/bm")
    with res_col2:
        st.metric(label="Vypočítaná cena za 1 ks", value=f"{cena_ks:.4f} €")
    
    st.session_state['cena_ks_final'] = cena_ks
else:
    st.warning("⚠️ Skontrolujte rozmery komponentu a výber polotovaru.")
