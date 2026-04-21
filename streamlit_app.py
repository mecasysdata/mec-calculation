import streamlit as st

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
