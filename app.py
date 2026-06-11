import streamlit as st
import pandas as pd
import plotly.express as px

# 1. KONFIGURASI HALAMAN UTAMA (Wajib Paling Atas)
st.set_page_config(
    page_title="Sistem Informasi ASG", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# STYLE CSS CUSTOM UNTUK METRIK DASHBOARD
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .metric-card {
        background-color: #ffffff; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04); border: 1px solid #e2e8f0; text-align: center;
        margin-bottom: 15px;
    }
    .metric-title { font-size: 13px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;}
    .metric-value { font-size: 28px; font-weight: 700; color: #1e3a8a; }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNGSI AMBIL DATA DARI GOOGLE SHEETS
url = "https://docs.google.com/spreadsheets/d/1-8ySRDAkrbbBMjBEiW3hXsNN3BMFe0OnWJqd9tXQRpg/export?format=csv"

@st.cache_data
def load_data_asg_final():
    df = pd.read_csv(url)
    df = df.dropna(how='all')
    
    # Bersihkan spasi di nama kolom tanpa mengubah huruf besar/kecil asli Excel kamu
    df.columns = [str(col).strip() for col in df.columns]
    
    # Konversi data angka TARIF secara aman
    if 'TARIF' in df.columns:
        df['TARIF_NUM'] = pd.to_numeric(df['TARIF'], errors='coerce').fillna(0)
    else:
        df['TARIF_NUM'] = 0
        
    if 'KILOMETER' in df.columns:
        df['KM_NUM'] = pd.to_numeric(df['KILOMETER'], errors='coerce').fillna(0)
    else:
        df['KM_NUM'] = 0
        
    # --- MEMBERSIHKAN FORMAT TANGGAL/BULAN/TAHUN GAIB DARI EXCEL ---
    # Fungsi pembantu untuk mengubah "2026.0" atau "1.0" menjadi "2026" atau "1" secara paksa
    def clean_date_values(series):
        # Konversi ke numeric dulu, hilangkan NaN dengan 0, ubah ke integer, lalu balikkan ke string teks biasa
        return pd.to_numeric(series, errors='coerce').fillna(0).astype(int).astype(str)

    if 'YEAR' in df.columns:
        df['YEAR_CLEAN'] = clean_date_values(df['YEAR'])
    else:
        df['YEAR_CLEAN'] = "2026"
        
    if 'MONTH' in df.columns:
        df['MONTH_CLEAN'] = clean_date_values(df['MONTH'])
    else:
        df['MONTH_CLEAN'] = "1"
        
    if 'DATE' in df.columns:
        df['DATE_CLEAN'] = clean_date_values(df['DATE'])
    else:
        df['DATE_CLEAN'] = "1"
        
    if 'STORE' in df.columns:
        df['STORE_CLEAN'] = df['STORE'].astype(str).str.strip()
    else:
        df['STORE_CLEAN'] = "UNKNOWN"
        
    return df

try:
    df = load_data_asg_final()
except Exception as e:
    st.error(f"Gagal memuat data dari Google Sheets: {e}")
    st.stop()


# =======================================================
# 3. SIDEBAR UTAMA & PEMBERIAN FILTER
# =======================================================
st.sidebar.image("https://asg-express.com/wp-content/uploads/2022/01/logo-asg-1.png", width=150)
st.sidebar.markdown("<br>", unsafe_allow_html=True)

st.sidebar.markdown("### 🗂️ NAVIGASI MENU")
pilihan_menu = st.sidebar.radio(
    "Pilih Halaman:",
    options=["Dashboard Utama", "Laporan Operasional Toko"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 FILTER DATA GLOBAL")

# Filter TAHUN (YEAR)
list_year = sorted([y for y in df['YEAR_CLEAN'].unique() if y != '0' and y != 'nan'])
selected_year = st.sidebar.multiselect("YEAR", options=list_year, default=list_year)

# Filter BULAN (MONTH)
list_month = sorted([m for m in df['MONTH_CLEAN'].unique() if m != '0' and m != 'nan'], key=lambda x: int(x) if x.isdigit() else 0)
selected_month = st.sidebar.multiselect("MONTH", options=list_month, default=list_month)

# Filter TANGGAL (DATE)
list_date = sorted([d for d in df['DATE_CLEAN'].unique() if d != '0' and d != 'nan'], key=lambda x: int(x) if x.isdigit() else 0)
selected_date = st.sidebar.multiselect("DATE (Tanggal)", options=list_date, default=list_date)

# Filter TOKO (STORE)
list_store = sorted([s for s in df['STORE_CLEAN'].unique() if s != 'nan' and s != 'None'])
selected_store = st.sidebar.multiselect("STORE (Toko/Cabang)", options=list_store, default=list_store)

# JALANKAN PROSES FILTERING DATA SECARA AMAN
df_filtered = df[
    (df['YEAR_CLEAN'].isin(selected_year)) &
    (df['MONTH_CLEAN'].isin(selected_month)) &
    (df['DATE_CLEAN'].isin(selected_date)) &
    (df['STORE_CLEAN'].isin(selected_store))
]


def format_id(angka):
    return f"{angka:,.0f}".replace(",", ".")

def format_persen(angka):
    return f"{angka:.1f}%"


# =======================================================
# KONDISI 1: DASHBOARD UTAMA
# =======================================================
if pilihan_menu == "Dashboard Utama":
    st.markdown("<h2 style='text-align: center; color: #1e3a8a; margin-bottom: 5px; font-family: sans-serif;'>DASHBOARD OPERASIONAL ASG</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 14px; margin-bottom: 30px;'>PT Alfa Sir Guna • Ringkasan Visual Grafik Performa</p>", unsafe_allow_html=True)
    
    if not df_filtered.empty:
        total_ritase = len(df_filtered)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Total Ritase</div><div class='metric-value'>{format_id(total_ritase)}</div><p style='color: #64748b; font-size: 11px; margin-top:5px;'>Count Order</p></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Total Sales (Tarif)</div><div class='metric-value'>Rp {format_id(df_filtered['TARIF_NUM'].sum())}</div><p style='color: #64748b; font-size: 11px; margin-top:5px;'>Sum Tarif</p></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Total Kilometer</div><div class='metric-value'>{format_id(df_filtered['KM_NUM'].sum())} KM</div><p style='color: #64748b; font-size: 11px; margin-top:5px;'>Sum Kilometer</p></div>", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        df_chart = df_filtered.groupby('DATE_CLEAN').agg(
            SALES_TOTAL=('TARIF_NUM', 'sum'),
            RITASE_TOTAL=('TARIF_NUM', 'count')
        ).reset_index()
        df_chart = df_chart.sort_values('DATE_CLEAN', key=lambda x: pd.to_numeric(x, errors='coerce'))
        
        grid_col1, grid_col2 = st.columns(2)
        cfg = {
            'plot_bgcolor': 'rgba(0,0,0,0)', 'paper_bgcolor': 'rgba(0,0,0,0)',
            'xaxis': {'showgrid': False, 'type': 'category', 'title': 'Tanggal (DATE)'}, 
            'yaxis': {'showgrid': True, 'gridcolor': '#e2e8f0'}
        }
        with grid_col1:
            fig1 = px.line(df_chart, x="DATE_CLEAN", y="SALES_TOTAL", title="TREN PENJUALAN HARIAN (SALES)", markers=True)
            fig1.update_traces(line_color='#1e3a8a', line_width=4)
            fig1.update_layout(**cfg)
            st.plotly_chart(fig1, use_container_width=True)
        with grid_col2:
            fig2 = px.line(df_chart, x="DATE_CLEAN", y="RITASE_TOTAL", title="TREN RITASE HARIAN (COUNT)", markers=True)
            fig2.update_traces(line_color='#10b981', line_width=4)
            fig2.update_layout(**cfg)
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("⚠️ Data hasil filter kosong. Silakan pilih/centang item filter di sidebar kiri.")


# =======================================================
# KONDISI 2: LAPORAN OPERASIONAL TOKO (RITASE, ACH SALES, MOBIL JALAN)
# =======================================================
elif pilihan_menu == "Laporan Operasional Toko":
    st.markdown("<h2 style='color: #1e3a8a; font-family: sans-serif; margin-bottom: 5px;'>LAPORAN OPERASIONAL PER TOKO</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; font-size: 14px; margin-bottom: 15px;'>Ringkasan Rata-rata Ritase, Ach Sales, dan Jumlah Armada Aktif</p>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    
    if not df_filtered.empty:
        # 1. Hitung Rata-rata Ritase harian per store
        df_ritase_harian = df_filtered.groupby(['STORE_CLEAN', 'DATE_CLEAN']).size().reset_index(name='RITASE_HARI')
        df_avg_ritase = df_ritase_harian.groupby('STORE_CLEAN')['RITASE_HARI'].mean().reset_index(name='AVG_RITASE')
        
        # 2. Hitung Total sales & Mobil unik (by NOPOL) per store
        nopol_col = 'NOPOL' if 'NOPOL' in df_filtered.columns else (df_filtered.columns[0])
        df_store_summary = df_filtered.groupby('STORE_CLEAN').agg(
            TOTAL_SALES=('TARIF_NUM', 'sum'),
            JUMLAH_MOBIL=(nopol_col, 'nunique')
        ).reset_index()
        
        df_report_toko = pd.merge(df_avg_ritase, df_store_summary, on='STORE_CLEAN')
        
        # 3. Hitung Ach Sales (%) -> Target rata-rata diset Rp 50.000.000 per toko
        ASUMSI_TARGET = 50000000
        df_report_toko['ACH_SALES'] = (df_report_toko['TOTAL_SALES'] / ASUMSI_TARGET) * 100
        
        # 4. Baris Total Akumulasi Terbawah (Grand Total)
        grand_total = pd.DataFrame([{
            'STORE_CLEAN': 'Grand Total / Average',
            'AVG_RITASE': df_report_toko['AVG_RITASE'].mean(),
            'TOTAL_SALES': df_report_toko['TOTAL_SALES'].sum(),
            'JUMLAH_MOBIL': df_filtered[nopol_col].nunique(),
            'ACH_SALES': (df_report_toko['TOTAL_SALES'].sum() / (ASUMSI_TARGET * len(df_report_toko))) * 100 if len(df_report_toko) > 0 else 0
        }])
        
        df_final_toko = pd.concat([df_report_toko, grand_total], ignore_index=True)
        
        # Format Akhir Tampilan Tabel
        df_tampil_toko = pd.DataFrame()
        df_tampil_toko['NAMA TOKO (STORE)'] = df_final_toko['STORE_CLEAN']
        df_tampil_toko['RATA-RATA RITASE / HARI'] = df_final_toko['AVG_RITASE'].apply(lambda x: f"{x:.1f} Rit")
        df_tampil_toko['TOTAL SALES (TARIF)'] = df_final_toko['TOTAL_SALES'].apply(format_id)
        df_tampil_toko['ACH SALES (%)'] = df_final_toko['ACH_SALES'].apply(format_persen)
        df_tampil_toko['ARMADA JALAN (BY NOPOL)'] = df_final_toko['JUMLAH_MOBIL'].apply(lambda x: f"{x} Mobil")
        
        st.write(f"💡 Menampilkan rekap operasional untuk **{len(df_report_toko)}** Toko aktif:")
        st.dataframe(df_tampil_toko, use_container_width=True, height=400)
        st.info("ℹ️ Catatan: Kolom 'ACH SALES (%)' dihitung dengan asumsi target Rp 50.000.000 per toko.")
    else:
        st.warning("⚠️ Data hasil filter kosong. Pastikan kotak filter di sidebar kiri sudah tercentang dengan benar.")