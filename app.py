import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. Page Configuration & Theme
st.set_page_config(
    page_title="ASG Operations & Expense Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Deep Orange & Gen Z CSS Style
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background-color: #fcfbfa; }
    .kpi-card { background: white; padding: 24px; border-radius: 16px; box-shadow: 0 4px 20px rgba(235, 94, 40, 0.05); border: 1px solid rgba(235, 94, 40, 0.08); transition: transform 0.2s ease; margin-bottom: 20px; }
    .kpi-title { color: #6c757d; font-size: 14px; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }
    .kpi-value { color: #ff5722; font-size: 28px; font-weight: 700; }
    .section-title { color: #212529; font-size: 20px; font-weight: 700; margin-top: 10px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# 2. DATA LOADING FUNCTIONS
@st.cache_data(ttl=600)
def load_sales_data():
    url = "https://docs.google.com/spreadsheets/d/1Z3sGqENFtjF-gGsRuN4lLUhmGZa5X1AbVx8Ueu-63YQ/gviz/tq?tqx=out:csv&sheet=LAPORAN"
    df = pd.read_csv(url)
    df.columns = [c.strip().upper() for c in df.columns]
    df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], dayfirst=True, errors='coerce')
    df['YEAR'] = df['TANGGAL'].dt.year.astype(int)
    df['MONTH_NAME'] = df['TANGGAL'].dt.strftime('%B')
    df['MONTH_NUM'] = df['TANGGAL'].dt.month
    df['DAY_NUM'] = df['TANGGAL'].dt.day.astype(int)
    return df

@st.cache_data(ttl=600)
def load_expense_data():
    url = "https://docs.google.com/spreadsheets/d/1ODK1VYWR6xtFGmpo6CYaLdtzucw2d4uKFDibj8DU3OE/gviz/tq?tqx=out:csv&sheet=PENGELUARAN"
    df = pd.read_csv(url)
    df.columns = [c.strip().upper() for c in df.columns]
    df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], dayfirst=True, errors='coerce')
    df['YEAR'] = df['TANGGAL'].dt.year.astype(int)
    df['MONTH_NAME'] = df['TANGGAL'].dt.strftime('%B')
    df['DAY_NUM'] = df['TANGGAL'].dt.day.astype(int)
    df['DEBIT'] = pd.to_numeric(df['DEBIT'].astype(str).str.replace(r'[Rp,]', '', regex=True), errors='coerce').fillna(0)
    return df

@st.cache_data(ttl=600)
def load_bbm_master():
    # Mengambil data dari spreadsheet baru
    url = "https://docs.google.com/spreadsheets/d/1TKznhfQwdPSdMu4dPxoMXis-3jR9QRCAqLAUzBAftpk/export?format=csv"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df

# 3. SIDEBAR
menu_pilihan = st.sidebar.radio("Pilih Halaman Dashboard:", ["📊 Performa Operasional ASG", "💸 Pengeluaran Operasional"])

# --- HALAMAN 1 (SALES) ---
if menu_pilihan == "📊 Performa Operasional ASG":
    df_cleaned = load_sales_data()
    st.title("SALES & RITASE DASHBOARD")
    st.dataframe(df_cleaned, use_container_width=True)

# --- HALAMAN 2 (PENGELUARAN + BBM) ---
elif menu_pilihan == "💸 Pengeluaran Operasional":
    # Membuat Tabs
    tab_utama, tab_bbm = st.tabs(["💰 Analisis Biaya Umum", "⛽ Monitoring BBM & KM"])
    
    with tab_utama:
        # [KODE LAMA KAMU UNTUK PENGELUARAN]
        df_expense = load_expense_data()
        st.title("PENGELUARAN OPERASIONAL")
        st.dataframe(df_expense, use_container_width=True)

    with tab_bbm:
        st.title("⛽ Monitoring BBM & KM")
        df_master = load_bbm_master()
        df_sales = load_sales_data()
        df_exp = load_expense_data()
        
        # Merge data KM dan Biaya
        df_km = df_sales.groupby('NOPOL')['ALL ONE WAY'].sum().reset_index()
        df_biaya = df_exp.groupby('NOPOL')['DEBIT'].sum().reset_index()
        
        df_master['NOPOL'] = df_master['NOPOL'].astype(str).str.strip().str.upper()
        
        merged = pd.merge(df_master, df_km, on='NOPOL', how='left').fillna(0)
        merged = pd.merge(merged, df_biaya, on='NOPOL', how='left').fillna(0)
        
        # Logika Status
        # Sesuaikan 'Rasio Standar Km/Liter' dengan nama kolom di sheet barumu
        merged['BATAS_MAKS'] = (merged['ALL ONE WAY'] / merged['Rasio Standar Km/Liter']) * 7000 
        merged['STATUS'] = merged.apply(lambda x: "Melebihi Batas" if x['DEBIT'] > x['BATAS_MAKS'] else "Masih Batas Aman", axis=1)
        
        # Styling
        def color_status(val):
            return 'background-color: #ff4b4b; color: white; font-weight: bold;' if val == 'Melebihi Batas' else 'background-color: #21c354; color: white; font-weight: bold;'
        
        st.dataframe(merged.style.map(color_status, subset=['STATUS']), use_container_width=True)
