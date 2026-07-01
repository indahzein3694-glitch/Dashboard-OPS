mport streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==============================================================================
# 1. PAGE CONFIGURATION & THEME STYLE
# ==============================================================================
st.set_page_config(
    page_title="ASG Operations & Expense Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background-color: #fcfbfa; }
    .kpi-card {
        background: white; padding: 24px; border-radius: 16px;
        box-shadow: 0 4px 20px rgba(235, 94, 40, 0.05);
        border: 1px solid rgba(235, 94, 40, 0.08);
        transition: transform 0.2s ease; margin-bottom: 20px;
    }
    .kpi-card:hover { transform: translateY(-4px); box-shadow: 0 6px 25px rgba(235, 94, 40, 0.1); }
    .kpi-title { color: #6c757d; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
    .kpi-value { color: #ff5722; font-size: 28px; font-weight: 700; }
    .section-title { color: #212529; font-size: 20px; font-weight: 700; margin-top: 10px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. DATA LOADING FUNCTIONS FROM MULTI-SPREADSHEETS
# ==============================================================================

@st.cache_data(ttl=600)
def load_master_data_kendaraan():
    sheet_id = "1TKznhfQwdPSdMu4dPxoMXis-3jR9QRCAqLAUzBAftpk"
    url_master = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=MASTER+KENDARAAN"
    url_harga = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=HARGA_BBM"
    try:
        df_m = pd.read_csv(url_master)
        df_m.columns = [c.strip().upper() for c in df_m.columns]
        if 'NOPOL' in df_m.columns:
            df_m['NOPOL_KEY'] = df_m['NOPOL'].astype(str).str.replace(' ', '', regex=False).str.replace('-', '', regex=False).str.upper()
        df_h = pd.read_csv(url_harga)
        df_h.columns = [c.strip().upper() for c in df_h.columns]
        return df_m, df_h
    except:
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=600)
def load_sales_data():
    sheet_id = "1Z3sGqENFtjF-gGsRuN4lLUhmGZa5X1AbVx8Ueu-63YQ"
    sheet_name = "LAPORAN"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        df = pd.read_csv(url)
        
        # Simpan nama asli kolom sebelum diubah ke uppercase untuk pelacakan posisi indeks
        raw_columns = list(df.columns)
        
        # Normalisasi nama kolom untuk kebutuhan pencarian teks biasa
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce', format='mixed')
        df = df.dropna(subset=['TANGGAL']).copy()
        
        if 'SALES' in df.columns:
            df['SALES'] = df['SALES'].astype(str).str.replace('Rp', '', regex=False).str.replace(',', '', regex=False).str.strip()
            df['SALES'] = pd.to_numeric(df['SALES'], errors='coerce').fillna(0)
            
        df['RITASE'] = pd.to_numeric(df['RITASE'], errors='coerce').fillna(0)
        df['YEAR'] = df['TANGGAL'].dt.year.astype(int)
        df['MONTH_NAME'] = df['TANGGAL'].dt.strftime('%B')
        df['MONTH_NUM'] = df['TANGGAL'].dt.month
        df['DAY_NUM'] = df['TANGGAL'].dt.day.astype(int)
        
        # ----------------------------------------------------------------------
        # SOLUSI TOTAL: AMBIL BERDASARKAN URUTAN KOLOM (INDEKS)
        # ----------------------------------------------------------------------
        # Angka 8 berarti Kolom ke-8 (Kolom H di Google Sheets). 
        # Jika kolom KM kamu ada di kolom F ganti jadi 6, jika di G ganti jadi 7, jika di I ganti jadi 9.
        target_column_index = 8 
        
        if len(raw_columns) >= target_column_index:
            actual_col_name = df.columns[target_column_index - 1]
            df['ALL_ONE_WAY_CLEANED'] = df[actual_col_name].astype(str).str.replace(',', '', regex=False)
            df['ALL_ONE_WAY_CLEANED'] = pd.to_numeric(df['ALL_ONE_WAY_CLEANED'], errors='coerce').fillna(0)
        else:
            df['ALL_ONE_WAY_CLEANED'] = 0
            
        if 'NO INVOICE' in df.columns:
            df['STORE'] = df['NO INVOICE'].fillna('TANPA NAMA').astype(str).str.strip().str.upper()
        elif 'STORE' in df.columns:
            df['STORE'] = df['STORE'].fillna('TANPA NAMA').astype(str).str.strip().str.upper()
        else:
            df['STORE'] = 'TANPA NAMA'
            
        df = df[df['STORE'].str.strip() != ''].copy()
        df = df[df['STORE'] != 'TANPA NAMA'].copy()
        
        df['NOPOL'] = df['NOPOL'].fillna('TANPA NOPOL').astype(str).str.strip()
        df['NOPOL_KEY'] = df['NOPOL'].str.replace(' ', '', regex=False).str.replace('-', '', regex=False).str.upper()
        return df
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_expense_data():
    sheet_id = "1ODK1VYWR6xtFGmpo6CYaLdtzucw2d4uKFDibj8DU3OE"
    sheet_name = "PENGELUARAN"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['TANGGAL']).copy()
        
        df['YEAR'] = df['TANGGAL'].dt.year.astype(int)
        df['MONTH_NAME'] = df['TANGGAL'].dt.strftime('%B')
        df['DAY_NUM'] = df['TANGGAL'].dt.day.astype(int)
        
        if 'DEBIT' in df.columns:
            df['DEBIT'] = df['DEBIT'].astype(str).str.replace('Rp', '', regex=False).str.replace(',', '', regex=False).str.strip()
            df['DEBIT'] = pd.to_numeric(df['DEBIT'], errors='coerce').fillna(0)
            
        df['STORE'] = df['STORE'].fillna('TANPA NAMA').astype(str).str.strip().str.upper()
        df = df[df['STORE'].str.strip() != ''].copy()
        
        df['NOPOL'] = df['NOPOL'].fillna('TANPA NOPOL').astype(str).str.strip()
        df['NOPOL_KEY'] = df['NOPOL'].str.replace(' ', '', regex=False).str.replace('-', '', regex=False).str.upper()
        df['NAMA'] = df['NAMA'].fillna('TANPA NAMA').astype(str).str.strip()
        return df
    except Exception as e:
        return pd.DataFrame()

# ==============================================================================
# 3. SIDEBAR NAVIGATION MENU
# ==============================================================================
st.sidebar.image("https://img.icons8.com/fluent/96/000000/dashboard.png", width=80)
st.sidebar.markdown("<h2 style='color: #ff5722; font-weight:700; margin-bottom:20px;'>MENU UTAMA</h2>", unsafe_allow_html=True)

menu_pilihan = st.sidebar.radio(
    "Pilih Halaman Dashboard:",
    ["📊 Performa Operasional ASG", "💸 Pengeluaran Operasional"]
)
st.sidebar.markdown("<hr style='border: 0.5px solid rgba(235, 94, 40, 0.1);'>", unsafe_allow_html=True)

# ==========================================
# HALAMAN 1: DASHBOARD PERFORMA OPERASIONAL
# ==========================================
if menu_pilihan == "📊 Performa Operasional ASG":
    df_cleaned = load_sales_data()
    
    if df_cleaned.empty:
        st.error("Gagal mengambil data Sales & Ritase. Pastikan spreadsheet diatur ke Publik.")
    else:
        st.sidebar.markdown("<h4 style='color: #ff5722;'>Filter Performa</h4>", unsafe_allow_html=True)
        
        year_options = sorted([int(y) for y in df_cleaned['YEAR'].unique() if y in [2024, 2025, 2026]])
        selected_years = st.sidebar.multiselect("Pilih YEAR (Tahun)", options=year_options, default=[])
        
        month_order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        month_options = [m for m in month_order if m in df_cleaned['MONTH_NAME'].unique()]
        selected_months = st.sidebar.multiselect("Pilih MONTH (Bulan)", options=month_options, default=[])
        
        date_options = sorted([int(d) for d in df_cleaned['DAY_NUM'].unique() if d > 0])
        selected_dates = st.sidebar.multiselect("Pilih DATE (Tanggal)", options=date_options, default=[])
        
        store_options = sorted([str(s) for s in df_cleaned['STORE'].unique() if str(s).strip() != ''])
        selected_stores = st.sidebar.multiselect("Pilih Store", options=store_options, default=[])
        
        df_filtered = df_cleaned.copy()
        if selected_years: df_filtered = df_filtered[df_filtered['YEAR'].isin(selected_years)]
        if selected_months: df_filtered = df_filtered[df_filtered['MONTH_NAME'].isin(selected_months)]
        if selected_dates: df_filtered = df_filtered[df_filtered['DAY_NUM'].isin(selected_dates)]
        if selected_stores: df_filtered = df_filtered[df_filtered['STORE'].isin(selected_stores)]
            
        st.markdown("<h1 style='color: #ff5722; font-weight:800; margin-bottom: 5px;'>SALES & RITASE DASHBOARD</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #6c757d; font-size: 15px; margin-bottom: 25px;'>Operasional ASG • Real-time Monitoring & Analysis</p>", unsafe_allow_html=True)
        
        total_sales = df_filtered['SALES'].sum()
        total_all_one_way = df_filtered['ALL_ONE_WAY_CLEANED'].sum()
        
        total_days = df_filtered['TANGGAL'].nunique()
        if total_days > 0:
            count_ritase_total = df_filtered[df_filtered['RITASE'] > 0]['RITASE'].count()
            active_nopol_per_day = df_filtered.groupby('TANGGAL')['NOPOL'].nunique().mean()
            ritase_index = (count_ritase_total / active_nopol_per_day / total_days) if active_nopol_per_day > 0 else 0
        else:
            ritase_index = 0
            
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1:
            st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Sales</div><div class="kpi-value">Rp {total_sales:,.0f}</div></div>', unsafe_allow_html=True)
        with kpi2:
            st.markdown(f'<div class="kpi-card"><div class="kpi-title">Ritase Index (Avg/Day)</div><div class="kpi-value">{ritase_index:.2f} <span style="font-size:14px; font-weight:400; color:#6c757d;">rit/truk</span></div></div>', unsafe_allow_html=True)
        with kpi3:
            st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Kilometer Rute</div><div class="kpi-value">{total_all_one_way:,.1f} <span style="font-size:14px; font-weight:400; color:#6c757d;">KM</span></div></div>', unsafe_allow_html=True)
            
        st.markdown("<div class='section-title'>Visualisasi Performa</div>", unsafe_allow_html=True)
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            st.markdown("<b style='color:#212529;'>Perbandingan Sales Tahun 2024 vs 2025 vs 2026</b>", unsafe_allow_html=True)
            df_sales_yr = df_filtered[df_filtered['YEAR'].isin([2024, 2025, 2026])].groupby('YEAR')['SALES'].sum().reset_index()
            df_sales_yr['YEAR'] = df_sales_yr['YEAR'].astype(str)
            fig_sales = px.bar(df_sales_yr, x='YEAR', y='SALES', color='YEAR', color_discrete_map={'2024': '#ffccbc', '2025': '#ffb09c', '2026': '#ff5722'}, text_auto=',d')
            fig_sales.update_layout(plot_bgcolor='white', paper_bgcolor='white', showlegend=False, xaxis_title=None, yaxis_title="Total Sales (Rp)", yaxis=dict(tickformat=",d"))
            st.plotly_chart(fig_sales, use_container_width=True)
        with row1_col2:
            st.markdown("<b style='color:#212529;'>Tren Ritase Bulanan (2024 vs 2025 vs 2026)</b>", unsafe_allow_html=True)
            df_ritase_trend = df_filtered[df_filtered['YEAR'].isin([2024, 2025, 2026])].groupby(['YEAR', 'MONTH_NUM', 'MONTH_NAME'])['RITASE'].sum().reset_index().sort_values(by='MONTH_NUM')
            df_ritase_trend['YEAR'] = df_ritase_trend['YEAR'].astype(str)
            fig_line = px.line(df_ritase_trend, x='MONTH_NAME', y='RITASE', color='YEAR', markers=True, color_discrete_map={'2024': '#ffccbc', '2025': '#ffb09c', '2026': '#ff5722'})
            fig_line.update_layout(plot_bgcolor='white', paper_bgcolor='white', xaxis_title=None, yaxis_title="Jumlah Ritase")
            st.plotly_chart(fig_line, use_container_width=True)
            
        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.markdown("<b style='color:#212529;'>Growth Sales (Pertumbuhan % YoY)</b>", unsafe_allow_html=True)
            df_growth = df_filtered[df_filtered['YEAR'].isin([2024, 2025, 2026])].groupby('YEAR')['SALES'].sum().reset_index()
            df_growth['GROWTH_%'] = df_growth['SALES'].pct_change() * 100
            df_growth['GROWTH_%'] = df_growth['GROWTH_%'].fillna(0)
            df_growth['YEAR'] = df_growth['YEAR'].astype(str)
            fig_growth = px.bar(df_growth, x='YEAR', y='GROWTH_%', text=df_growth['GROWTH_%'].apply(lambda x: f"{x:+.1f}%" if x != 0 else "0%"), color_discrete_sequence=['#ff7043'])
            fig_growth.update_layout(plot_bgcolor='white', paper_bgcolor='white', xaxis_title=None, yaxis_title="Pertumbuhan (%)")
            st.plotly_chart(fig_growth, use_container_width=True)
        with row2_col2:
            st.markdown("<b style='color:#212529;'>Peringkat Sales per Store</b>", unsafe_allow_html=True)
            df_store_sales = df_filtered.groupby('STORE')['SALES'].sum().reset_index().sort_values(by='SALES', ascending=True)
            fig_horiz = px.bar(df_store_sales, x='SALES', y='STORE', orientation='h', text_auto=',d')
            fig_horiz.update_traces(marker_color='#ff7043')
            fig_horiz.update_layout(plot_bgcolor='white', paper_bgcolor='white', xaxis_title="Total Sales (Rp)", yaxis_title=None)
            st.plotly_chart(fig_horiz, use_container_width=True)

# ==========================================
# HALAMAN 2: DASHBOARD PENGELUARAN OPERASIONAL
# ==========================================
elif menu_pilihan == "💸 Pengeluaran Operasional":
    df_expense = load_expense_data()
    df_sales_for_km = load_sales_data()
    df_master_mbl, df_harga_live = load_master_data_kendaraan()
    
    if df_expense.empty:
        st.error("Gagal mengambil data Pengeluaran. Pastikan link Google Sheet Pengeluaran sudah Publik.")
    else:
        st.markdown("<h1 style='color: #ff5722; font-weight:800; margin-bottom: 5px;'>PENGELUARAN OPERASIONAL</h1>", unsafe_allow_html=True)
        
        st.markdown("<b style='color:#ff5722;'>⚙️ PANEL FILTER DATA PENGELUARAN</b>", unsafe_allow_html=True)
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            exp_year_options = sorted([int(y) for y in df_expense['YEAR'].unique() if y > 0])
            sel_exp_years = st.multiselect("Pilih YEAR (Tahun)", options=exp_year_options, key="exp_yr")
            exp_store_options = sorted([str(s) for s in df_expense['STORE'].unique() if str(s).strip() != ''])
            sel_exp_stores = st.multiselect("Pilih STORE", options=exp_store_options, key="exp_st")
        with f_col2:
            month_order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            exp_month_options = [m for m in month_order if m in df_expense['MONTH_NAME'].unique()]
            sel_exp_months = st.multiselect("Pilih MONTH (Bulan)", options=exp_month_options, key="exp_mo")
            exp_nama_options = sorted([str(n) for n in df_expense['NAMA'].unique() if str(n).strip() != ''])
            sel_exp_namas = st.multiselect("Pilih NAMA", options=exp_nama_options, key="exp_nm")
        with f_col3:
            exp_date_options = sorted([int(d) for d in df_expense['DAY_NUM'].unique() if d > 0])
            sel_exp_dates = st.multiselect("Pilih DATE (Tanggal)", options=exp_date_options, key="exp_dt")
        
        df_exp_filtered = df_expense.copy()
        df_sales_filtered = df_sales_for_km.copy()
        
        if sel_exp_years:
            df_exp_filtered = df_exp_filtered[df_exp_filtered['YEAR'].isin(sel_exp_years)]
            df_sales_filtered = df_sales_filtered[df_sales_filtered['YEAR'].isin(sel_exp_years)]
        if sel_exp_months:
            df_exp_filtered = df_exp_filtered[df_exp_filtered['MONTH_NAME'].isin(sel_exp_months)]
            df_sales_filtered = df_sales_filtered[df_sales_filtered['MONTH_NAME'].isin(sel_exp_months)]
        if sel_exp_dates:
            df_exp_filtered = df_exp_filtered[df_exp_filtered['DAY_NUM'].isin(sel_exp_dates)]
            df_sales_filtered = df_sales_filtered[df_sales_filtered['DAY_NUM'].isin(sel_exp_dates)]
        if sel_exp_stores:
            df_exp_filtered = df_exp_filtered[df_exp_filtered['STORE'].isin(sel_exp_stores)]
            df_sales_filtered = df_sales_filtered[df_sales_filtered['STORE'].isin(sel_exp_stores)]
        if sel_exp_namas:
            df_exp_filtered = df_exp_filtered[df_exp_filtered['NAMA'].isin(sel_exp_namas)]
            
        total_debit = df_exp_filtered['DEBIT'].sum()
        df_valid_nopol = df_exp_filtered[(df_exp_filtered['NOPOL'].str.upper() != 'TANPA NOPOL') & (df_exp_filtered['NOPOL'].str.strip() != '')]
        unique_nopol_count = df_valid_nopol['NOPOL'].nunique()
        
        exp_kpi1, exp_kpi2 = st.columns(2)
        with exp_kpi1:
            st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Pengeluaran</div><div class="kpi-value">Rp {total_debit:,.0f}</div></div>', unsafe_allow_html=True)
        with exp_kpi2:
            st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Nopol Aktif</div><div class="kpi-value">{unique_nopol_count:,.0f} <span style="font-size:14px; font-weight:400; color:#6c757d;">Unit Armada</span></div></div>', unsafe_allow_html=True)
            
        st.markdown("<div class='section-title'>⚠️ Kontrol Batasan Efisiensi BBM HPP (KM/Liter)</div>", unsafe_allow_html=True)
        
        if not df_master_mbl.empty:
            bbm_col_master = [c for c in df_master_mbl.columns if 'BBM' in c or 'BAHAN' in c]
            mobil_col_master = [c for c in df_master_mbl.columns if 'MOBIL' in c or 'ARMADA' in c]
            rasio_col_master = [c for c in df_master_mbl.columns if 'RASIO' in c or 'BATAS' in c]
            
            if bbm_col_master and rasio_col_master:
                nama_kolom_bbm = bbm_col_master[0]
                nama_kolom_rasio = rasio_col_master[0]
                nama_kolom_mobil = mobil_col_master[0] if mobil_col_master else df_master_mbl.columns[2]
                
                map_nopol_ke_nopol_asli = dict(zip(df_master_mbl['NOPOL_KEY'], df_master_mbl['NOPOL']))
                map_nopol_ke_mobil = dict(zip(df_master_mbl['NOPOL_KEY'], df_master_mbl[nama_kolom_mobil]))
                map_nopol_ke_bbm = dict(zip(df_master_mbl['NOPOL_KEY'], df_master_mbl[nama_kolom_bbm]))
                map_nopol_ke_rasio = dict(zip(df_master_mbl['NOPOL_KEY'], pd.to_numeric(df_master_mbl[nama_kolom_rasio], errors='coerce').fillna(0)))
                
                harga_bbm_dict = {'SOLAR': 6800, 'PERTALITE': 10000, 'PERTAMAX': 12500, 'DEXLITE': 12700}
                
                df_bbm_only = df_exp_filtered[df_exp_filtered['NAMA'].str.upper().str.contains("BAHAN BAKAR MINYAK HPP", na=False)]
                
                if df_bbm_only.empty:
                    st.info("ℹ️ Belum ada data pemakaian BBM HPP pada filter saat ini.")
                else:
                    df_bbm_sum = df_bbm_only.groupby('NOPOL_KEY')['DEBIT'].sum().reset_index().rename(columns={'DEBIT': 'RUPIAH_BBM'})
                    
                    if 'ALL_ONE_WAY_CLEANED' in df_sales_filtered.columns and 'RITASE' in df_sales_filtered.columns:
                        df_sales_filtered['KM_JALAN_ASLI'] = df_sales_filtered['ALL_ONE_WAY_CLEANED'] * df_sales_filtered['RITASE']
                        df_km_sum = df_sales_filtered.groupby('NOPOL_KEY')['KM_JALAN_ASLI'].sum().reset_index().rename(columns={'KM_JALAN_ASLI': 'KM_ONE_WAY'})
                    else:
                        df_km_sum = pd.DataFrame(columns=['NOPOL_KEY', 'KM_ONE_WAY'])
                    
                    df_final_calc = pd.merge(df_bbm_sum, df_km_sum, on='NOPOL_KEY', how='outer').fillna(0)
                    df_final_calc = df_final_calc[df_final_calc['NOPOL_KEY'].isin(map_nopol_ke_nopol_asli.keys())].copy()
                    
                    if not df_final_calc.empty:
                        df_final_calc['NOPOL_ASLI'] = df_final_calc['NOPOL_KEY'].map(map_nopol_ke_nopol_asli)
                        df_final_calc['TIPE_MOBIL'] = df_final_calc['NOPOL_KEY'].map(map_nopol_ke_mobil)
                        df_final_calc['JENIS_BBM'] = df_final_calc['NOPOL_KEY'].map(map_nopol_ke_bbm)
                        df_final_calc['TARGET_RASIO_RIIL'] = df_final_calc['NOPOL_KEY'].map(map_nopol_ke_rasio)
                        df_final_calc['HARGA_BBM_RIIL'] = df_final_calc['JENIS_BBM'].str.strip().str.upper().map(harga_bbm_dict).fillna(10000)
                        
                        df_final_calc['JARAK_REAL_PP'] = df_final_calc['KM_ONE_WAY'] * 1.67
                        df_final_calc['ESTIMASI_LITER'] = df_final_calc['RUPIAH_BBM'] / df_final_calc['HARGA_BBM_RIIL']
                        df_final_calc['RASIO_LAPANGAN_KM_L'] = df_final_calc.apply(lambda r: r['JARAK_REAL_PP'] / r['ESTIMASI_LITER'] if r['ESTIMASI_LITER'] > 0 else 0, axis=1)
                        
                        df_final_calc['STATUS'] = df_final_calc.apply(
                            lambda r: "⚠️ BOROS / OVER BUDGET" if r['RASIO_LAPANGAN_KM_L'] < r['TARGET_RASIO_RIIL'] and r['ESTIMASI_LITER'] > 0 else ("✅ AMAN" if r['ESTIMASI_LITER'] > 0 else "Data Tidak Lengkap"), axis=1
                        )
                        
                        df_view_bbm = pd.DataFrame()
                        df_view_bbm['NO POLISI'] = df_final_calc['NOPOL_ASLI']
                        df_view_bbm['TIPE MOBIL'] = df_final_calc['TIPE_MOBIL']
                        df_view_bbm['TARGET RASIO'] = df_final_calc['TARGET_RASIO_RIIL']
                        df_view_bbm['TOTAL BELANJA BBM'] = df_final_calc['RUPIAH_BBM']
                        df_view_bbm['KM TOTAL RUTE'] = df_final_calc['KM_ONE_WAY']
                        df_view_bbm['RASIO LAPANGAN (KM/L)'] = df_final_calc['RASIO_LAPANGAN_KM_L']
                        df_view_bbm['STATUS'] = df_final_calc['STATUS']
                        
                        st.dataframe(df_view_bbm, use_container_width=True, hide_index=True)
            else:
                st.warning("Struktur master data kendaraan tidak sesuai ekspektasi.")
        else:
            st.warning("Data Master Kendaraan gagal dimuat.")
            
        st.markdown("<br><div class='section-title'>Data List Pengeluaran</div>", unsafe_allow_html=True)
        df_list_tabel = df_exp_filtered.groupby(['STORE', 'NAMA', 'NOPOL'])['DEBIT'].sum().reset_index().sort_values(by='DEBIT', ascending=False)
        st.dataframe(df_list_tabel, use_container_width=True, hide_index=True)

st.markdown("<p style='text-align: center; color: #a0aec0; font-size: 12px;'>Dashboard Multi-Spreadsheet • Built with Streamlit</p>", unsafe_allow_html=True)
