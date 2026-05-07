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


