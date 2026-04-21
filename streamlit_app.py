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

# --- 5. FINÁLNY VÝSTUP (Pre ďalšie výpočty) ---
if vyber == moznost_novy and (not novy_meno or not novy_krajina):
    st.info("Zadajte údaje pre nového zákazníka v riadku vyššie.")
    st.stop()

st.success(f"Aktuálny výber: **{final_zakaznik}** | Krajina: **{final_krajina}** | Lojalita: **{final_lojalita}**")
st.divider()

# --- 6. RIADOK PRE POLOŽKU (Item, Náročnosť, KS, Tvar) ---
st.subheader("Špecifikácia položky")

# Hlavné stĺpce pre základné atribúty
r1, r2, r3, r4 = st.columns([2, 1, 1, 1.5])

with r1:
    item_nazov = st.text_input("ITEM (Označenie komponentu)", placeholder="napr. Hriadeľ 001")

with r2:
    narocnost = st.selectbox("Náročnosť výroby", options=[1, 2, 3, 4, 5])

with r3:
    pocet_ks = st.number_input("Počet kusov (KS)", min_value=1, step=1, value=1)

with r4:
    tvar = st.selectbox("Tvar", options=["KR", "STV"])

# --- 7. DYNAMICKÉ POLIA PRE ROZMERY ---
# Vytvoríme riadok pre rozmery, ktorý sa mení podľa "tvar"
st.write("**Rozmery (mm):**")
dist1, dist2, dist3, dist_prazdny = st.columns([1, 1, 1, 4])

# Inicializácia premenných pre rozmery
rozmer_D = 0.0
rozmer_L = 0.0
rozmer_S = 0.0
rozmer_V = 0.0

if tvar == "KR":
    with dist1:
        rozmer_D = st.number_input("D", min_value=0.0, format="%.2f", help="Priemer v mm")
    with dist2:
        rozmer_L = st.number_input("L", min_value=0.0, format="%.2f", help="Dĺžka v mm")
    # Tretie pole ostane prázdne pri KR

elif tvar == "STV":
    with dist1:
        rozmer_D = st.number_input("D/P", min_value=0.0, format="%.2f", help="Dĺžka/Priemer v mm")
    with dist2:
        rozmer_S = st.number_input("S", min_value=0.0, format="%.2f", help="Šírka v mm")
    with dist3:
        rozmer_V = st.number_input("V", min_value=0.0, format="%.2f", help="Výška v mm")

st.divider()

# --- UKÁŽKA ZOSBIERANÝCH DÁT (na kontrolu) ---
st.write(f"### Sumár položky:")
summary_cols = st.columns(4)
summary_cols[0].metric("Položka", item_nazov)
summary_cols[1].metric("Náročnosť", narocnost)
summary_cols[2].metric("Kusy", pocet_ks)
summary_cols[3].metric("Tvar", tvar)
