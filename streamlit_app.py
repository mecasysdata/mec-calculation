mport streamlit as st

st.title("MEC Calculation")
st.write("Vitajte vo vašej aplikácii na výpočet cien!")

cena = st.number_input("Zadajte základnú cenu", value=0.0)
st.write(f"Zadaná cena je: {cena}")
