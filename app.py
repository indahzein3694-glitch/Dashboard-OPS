import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="ASG Operations Dashboard", page_icon="📊", layout="wide")

# CSS Styling
st.markdown("""
    <style>
    .kpi-card { background: white; padding: 20px; border-radius: 12px; border-left: 5px solid #ff5722; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .kpi-title { color: #6c757d; font-size: 12px; text-transform: uppercase; font-weight: bold; }
    .kpi-value { color: #ff5722; font-size: 24px; font-weight: bold; }
    .section-title { font-size: 18px; font-weight: bold; margin-top: 20px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- DATA LOADERS ---
@st.cache_data(ttl=600)
def load_all_data():
    try:
        # Sheet 1: Sales/Ritase
        df_sales = pd.read_csv("https://docs.google.com/spreadsheets/d/1Z3sGqENFtjF-gGsRuN4lLUhmGZa5X1AbVx8Ueu-63YQ/gviz/tq?tqx=out:csv&sheet=LAPORAN")
        # Sheet 2: Pengeluaran
        df_exp = pd.read_csv("https://docs.google.com/spreadsheets/d/1ODK1VYWR6xtFGmpo6CYaLdtzucw2d4uKFDibj8DU3OE/gviz/tq?tqx=out:csv&sheet=PENGELUARAN")
        # Sheet 3: Master BBM
        df_bbm = pd.read_csv("https://docs.google.com/spreadsheets/d/1TKznhfQwdPSdMu4dPxoMXis-3jR9QRCAqLAUzBAftpk/gviz/tq?tqx=out:csv&sheet=Sheet1")
        
        for df in [df_sales, df_exp, df_bbm]:
            df.columns = df.columns.str.strip().str.upper()
        return df_sales, df_exp, df_bbm
    except:
        return None, None, None

# --- APP START ---
df_sales, df_exp, df_bbm = load_all_data()

menu = st.sidebar.radio("MENU UTAMA", ["📊 Performa Sales", "💸 Pengeluaran & BBM"])

# --- HALAMAN 1: SALES ---
if menu == "📊 Performa Sales":
    st.title("📊 Performa Operasional ASG")
    if df_sales is not None:
        st.write("Gunakan filter di sidebar untuk melihat data.")
        st.dataframe(df_sales, use_container_width=True)
    else:
        st.error("Data tidak ditemukan.")

# --- HALAMAN 2: PENGELUARAN & BBM ---
elif menu == "💸 Pengeluaran & BBM":
    st.title("💸 Pengeluaran & Pemantauan BBM")
    tab1, tab2 = st.tabs(["💰 Analisis Pengeluaran", "⛽ Monitoring BBM per Nopol"])
    
    with tab1:
        if df_exp is not None:
            st.dataframe(df_exp, use_container_width=True)
            
    with tab2:
        if df_bbm is not None and df_sales is not None and df_exp is not None:
            # Kalkulasi Gabungan
            df_km = df_sales.groupby('NOPOL')['ALL ONE WAY'].sum().reset_index()
            df_biaya = df_exp.groupby('NOPOL')['DEBIT'].sum().reset_index()
            
            # Merge Master
            merged = pd.merge(df_bbm, df_km, on='NOPOL', how='left').fillna(0)
            merged = pd.merge(merged, df_biaya, on='NOPOL', how='left').fillna(0)
            
            # Logika Status BBM (Rasio Standar Km/Liter)
            # Batas: (KM / Rasio) * Harga per Liter (Asumsi 6.800)
            merged['BATAS_MAKS'] = (merged['ALL ONE WAY'] / merged['RASIO STANDAR KM/LITER']) * 6800
            merged['STATUS'] = merged.apply(
                lambda x: "Melebihi Batas" if x['DEBIT'] > x['BATAS_MAKS'] else "Masih Batas Aman", axis=1
            )
            
            # Tabel dengan warna
            def color_status(val):
                return 'background-color: #ff4b4b; color: white;' if val == 'Melebihi Batas' else 'background-color: #21c354; color: white;'
            
            st.dataframe(merged.style.map(color_status, subset=['STATUS']), use_container_width=True)
        else:
            st.warning("Data belum dimuat.")
