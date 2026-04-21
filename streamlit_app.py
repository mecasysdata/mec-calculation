import streamlit as st
#zaciatok aplikacie
# Vytvoríme dva stĺpce: prvý pre logo (šírka 1) a druhý pre text (šírka 3)
# Pomer 1:3 zabezpečí, že logo nebude príliš dominantné
col1, col2 = st.columns([1, 3])

with col1:
    st.image("logo.png")

with col2:
    st.title("MEC Calculation")
    st.write("Vitajte vo vašej aplikácii na výpočet cien!")

# Tu môžete pokračovať so zvyškom aplikácie (už mimo stĺpcov)
st.divider() # Pridá jemnú deliacu čiaru

st.divider() # Tá čiara, o ktorej ste písali

# Vytvoríme dva stĺpce pre Dátum a Označenie
col_date, col_ref = st.columns([1, 1])

with col_date:
    # Atribút Dátum - predvolene nastavený na dnešok
    datum_ponuky = st.date_input("Dátum", help="Zadajte dátum vytvorenia ponuky")

with col_ref:
    # Atribút Označenie cenovej ponuky - voľný textový vstup
    oznacenie_ponuky = st.text_input("Označenie cenovej ponuky", placeholder="napr. CP-2024-001")

# Len pre kontrolu si môžeme vypísať, čo užívateľ zadal (neskôr to môžeme zmazať)
st.write(f"Pripravujete ponuku: **{oznacenie_ponuky}** zo dňa {datum_ponuky.strftime('%d.%m.%Y')}")
