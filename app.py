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

# --- DATA LOADERS (DENGAN ERROR HANDLING) ---
@st.cache_data(ttl=600)
def load_all_data():
    try:
        # Load 3 Sheet
        df_sales = pd.read_csv("https://docs.google.com/spreadsheets/d/1Z3sGqENFtjF-gGsRuN4lLUhmGZa5X1AbVx8Ueu-63YQ/gviz/tq?tqx=out:csv&sheet=LAPORAN")
        df_exp = pd.read_csv("https://docs.google.com/spreadsheets/d/1ODK1VYWR6xtFGmpo6CYaLdtzucw2d4uKFDibj8DU3OE/gviz/tq?tqx=out:csv&sheet=PENGELUARAN")
        df_bbm = pd.read_csv("https://docs.google.com/spreadsheets/d/1TKznhfQwdPSdMu4dPxoMXis-3jR9QRCAqLAUzBAftpk/gviz/tq?tqx=out:csv&sheet=Sheet1")
        
        # Standardisasi kolom
        for df in [df_sales, df_exp, df_bbm]:
            df.columns = df.columns.str.strip().str.upper()
        
        return df_sales, df_exp, df_bbm
    except Exception as e:
        st.error(f"Error memuat data: {e}")
        return None, None, None

# --- SIDEBAR ---
menu = st.sidebar.radio("MENU UTAMA", ["📊 Performa Sales", "💸 Pengeluaran & BBM"])
df_sales, df_exp, df_bbm = load_all_data()

# --- HALAMAN 1: SALES ---
if menu == "📊 Performa Sales":
    if df_sales is not None:
        st.title("📊 Performa Operasional ASG")
        # Masukkan kembali logika filter & grafik sales kamu di sini
        st.write("Data Sales dimuat dengan sukses. Silakan tambahkan kembali komponen grafik favoritmu.")
        st.dataframe(df_sales.head())

# --- HALAMAN 2: PENGELUARAN & BBM ---
elif menu == "💸 Pengeluaran & BBM":
    st.title("💸 Pengeluaran & Pemantauan BBM")
    tab1, tab2 = st.tabs(["💰 Analisis Pengeluaran", "⛽ Monitoring BBM per Nopol"])
    
    with tab1:
        if df_exp is not None:
            st.subheader("Data Pengeluaran Operasional")
            st.dataframe(df_exp, use_container_width=True)
            
    with tab2:
        if df_bbm is not None and df_sales is not None and df_exp is not None:
            st.subheader("Analisis Efisiensi BBM")
            
            # Persiapan Data Gabungan
            df_km = df_sales.groupby('NOPOL')['ALL ONE WAY'].sum().reset_index()
            df_biaya = df_exp.groupby('NOPOL')['DEBIT'].sum().reset_index()
            
            df_master = df_bbm.copy()
            df_master['NOPOL'] = df_master['NOPOL'].astype(str).str.strip().str.upper()
            
            # Join data
            merged = pd.merge(df_master, df_km, on='NOPOL', how='left').fillna(0)
            merged = pd.merge(merged, df_biaya, on='NOPOL', how='left').fillna(0)
            
            # Kalkulasi Batas (Asumsi 6800/liter)
            merged['BATAS_MAKS_BIAYA'] = (merged['ALL ONE WAY'] / merged['RASIO STANDAR KM/LITER']) * 6800
            merged['STATUS'] = merged.apply(lambda x: "Melebihi Batas" if x['DEBIT'] > x['BATAS_MAKS_BIAYA'] else "Masih Batas Aman", axis=1)
            
            # Styling
            def color_status(val):
                return 'background-color: #ff4b4b; color: white;' if val == 'Melebihi Batas' else 'background-color: #21c354; color: white;'
            
            # Tampilkan Tabel
            st.dataframe(merged.style.map(color_status, subset=['STATUS']), use_container_width=True)
        else:
            st.warning("Data belum siap.")
