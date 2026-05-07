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
# --- 3. RIADOK S ATRIBÚTMI ---
# Vytvoríme si stĺpce, aby sme mohli dávať prvky vedľa seba
col1, col2, col3, col4 = st.columns(4)

with col1:
    # Atribút Dátum: 
    # - label: "Dátum" (názov políčka)
    # - value: defaultne nastavený na dnešok (datetime.date.today())
    import datetime
    datum = st.date_input("Dátum", datetime.date.today())

with col2:
    # Atribút Ponuka:
    # - label: "Označenie CP" (názov, ktorý uvidí používateľ)
    # - value: "" (necháme prázdne, aby používateľ mohol písať)
    ponuka = st.text_input("Označenie CP")
