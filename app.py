import streamlit as st
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

# Custom Deep Orange & Gen Z CSS Style
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=400;500;600;700&display=swap');
    
    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Main Background */
    .stApp {
        background-color: #fcfbfa;
    }
    
    /* Card Styles */
    .kpi-card {
        background: white;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(235, 94, 40, 0.05);
        border: 1px solid rgba(235, 94, 40, 0.08);
        transition: transform 0.2s ease;
        margin-bottom: 20px;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 6px 25px rgba(235, 94, 40, 0.1);
    }
    .kpi-title {
        color: #6c757d;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    .kpi-value {
        color: #ff5722;
        font-size: 28px;
        font-weight: 700;
    }
    
    /* Section Title */
    .section-title {
        color: #212529;
        font-size: 20px;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. DATA LOADING FUNCTIONS FROM MULTI-SPREADSHEETS
# ==============================================================================

# --- Load Master Kendaraan & Harga BBM ---
@st.cache_data(ttl=600)
def load_master_data_kendaraan():
    sheet_id = "1TKznhfQwdPSdMu4dPxoMXis-3jR9QRCAqLAUzBAftpk"
    
    # Ambil Sheet Master Kendaraan (Lembar ke-1)
    url_master = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=MASTER+KENDARAAN"
    # Ambil Sheet Harga BBM (Lembar ke-2)
    url_harga = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=HARGA_BBM"
    
    try:
        df_m = pd.read_csv(url_master)
        df_m.columns = [c.strip().upper() for c in df_m.columns]
        if 'NOPOL' in df_m.columns:
            df_m['NOPOL_KEY'] = df_m['NOPOL'].astype(str).str.replace(' ', '', regex=False).str.upper()
            
        df_h = pd.read_csv(url_harga)
        df_h.columns = [c.strip().upper() for c in df_h.columns]
        
        return df_m, df_h
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

# --- Load Laporan Sales & Ritase (Total KM) ---
@st.cache_data(ttl=600)
def load_sales_data():
    sheet_id = "1Z3sGqENFtjF-gGsRuN4lLUhmGZa5X1AbVx8Ueu-63YQ"
    sheet_name = "LAPORAN"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip().upper() for c in df.columns]
        
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['TANGGAL']).copy()
        
        if 'SALES' in df.columns:
            df['SALES'] = df['SALES'].astype(str).str.replace('Rp', '', regex=False).str.replace(',', '', regex=False).str.strip()
            df['SALES'] = pd.to_numeric(df['SALES'], errors='coerce').fillna(0)
            
        df['RITASE'] = pd.to_numeric(df['RITASE'], errors='coerce').fillna(0)
        df['YEAR'] = df['TANGGAL'].dt.year.astype(int)
        df['MONTH_NAME'] = df['TANGGAL'].dt.strftime('%B')
        df['MONTH_NUM'] = df['TANGGAL'].dt.month
        df['DAY_NUM'] = df['TANGGAL'].dt.day.astype(int)
        
        all_one_way_col = [c for c in df.columns if 'ONE WAY' in c]
        if all_one_way_col:
            df['ALL ONE WAY'] = df[all_one_way_col[0]].astype(str).str.replace(',', '', regex=False)
            df['ALL ONE WAY'] = pd.to_numeric(df['ALL ONE WAY'], errors='coerce').fillna(0)
        else:
            df['ALL ONE WAY'] = 0
            
        if 'NO INVOICE' in df.columns:
            df['STORE'] = df['NO INVOICE'].fillna('TANPA NAMA').astype(str).str.strip().str.upper()
        elif 'STORE' in df.columns:
            df['STORE'] = df['STORE'].fillna('TANPA NAMA').astype(str).str.strip().str.upper()
        else:
            df['STORE'] = 'TANPA NAMA'
            
        # Saring baris hantu kosong
        df = df[df['STORE'].str.strip() != ''].copy()
        df = df[df['STORE'] != 'TANPA NAMA'].copy()
        df = df[df['STORE'] != 'NAN'].copy()
            
        df['NOPOL'] = df['NOPOL'].fillna('TANPA NOPOL').astype(str).str.strip()
        df['NOPOL_KEY'] = df['NOPOL'].str.replace(' ', '', regex=False).str.upper()
        return df
    except Exception as e:
        return pd.DataFrame()

# --- Load Pengeluaran Operasional ---
@st.cache_data(ttl=600)
def load_expense_data():
    sheet_id = "1ODK1VYWR6xtFGmpo6CYaLdtzucw2d4uKFDibj8DU3OE"
    sheet_name = "PENGELUARAN"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip().upper() for c in df.columns]
        
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['TANGGAL']).copy()
        
        df['YEAR'] = df['TANGGAL'].dt.year.astype(int)
        df['MONTH_NAME'] = df['TANGGAL'].dt.strftime('%B')
        df['DAY_NUM'] = df['TANGGAL'].dt.day.astype(int)
        
        if 'DEBIT' in df.columns:
            df['DEBIT'] = df['DEBIT'].astype(str).str.replace('Rp', '', regex=False).str.replace(',', '', regex=False).str.strip()
            df['DEBIT'] = pd.to_numeric(df['DEBIT'], errors='coerce').fillna(0)
            
        df['STORE'] = df['STORE'].fillna('TANPA NAMA').astype(str).str.strip().str.upper()
        
        # Saring baris hantu kosong
        df = df[df['STORE'].str.strip() != ''].copy()
        df = df[df['STORE'] != 'TANPA NAMA'].copy()
        df = df[df['STORE'] != 'NAN'].copy()
        
        df['NOPOL'] = df['NOPOL'].fillna('TANPA NOPOL').astype(str).str.strip()
        df['NOPOL_KEY'] = df['NOPOL'].str.replace(' ', '', regex=False).str.upper()
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
        if selected_years:
            df_filtered = df_filtered[df_filtered['YEAR'].isin(selected_years)]
        if selected_months:
            df_filtered = df_filtered[df_filtered['MONTH_NAME'].isin(selected_months)]
        if selected_dates:
            df_filtered = df_filtered[df_filtered['DAY_NUM'].isin(selected_dates)]
        if selected_stores:
            df_filtered = df_filtered[df_filtered['STORE'].isin(selected_stores)]
            
        st.markdown("<h1 style='color: #ff5722; font-weight:800; margin-bottom: 5px;'>SALES & RITASE DASHBOARD</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #6c757d; font-size: 15px; margin-bottom: 25px;'>Operasional ASG • Real-time Monitoring & Analysis</p>", unsafe_allow_html=True)
        
        total_sales = df_filtered['SALES'].sum()
        total_all_one_way = df_filtered['ALL ONE WAY'].sum()
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
            st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total All One Way</div><div class="kpi-value">{total_all_one_way:,.0f} <span style="font-size:14px; font-weight:400; color:#6c757d;">KM</span></div></div>', unsafe_allow_html=True)
            
        st.markdown("<div class='section-title'>Visualisasi Performa</div>", unsafe_allow_html=True)
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            st.markdown("<b style='color:#212529;'>Perbandingan Sales Tahun 2024 vs 2025 vs 2026</b>", unsafe_allow_html=True)
            df_sales_yr = df_filtered[df_filtered['YEAR'].isin([2024, 2025, 2026])].groupby('YEAR')['SALES'].sum().reset_index()
            df_sales_yr['YEAR'] = df_sales_yr['YEAR'].astype(str)
            
            fig_sales = px.bar(df_sales_yr, x='YEAR', y='SALES', color='YEAR', color_discrete_map={'2024': '#ffccbc', '2025': '#ffb09c', '2026': '#ff5722'}, text_auto=',d')
            fig_sales.update_layout(plot_bgcolor='white', paper_bgcolor='white', margin=dict(t=20, b=20, l=20, r=20), showlegend=False, xaxis_title=None, yaxis_title="Total Sales (Rp)", yaxis=dict(tickformat=",d"))
            st.plotly_chart(fig_sales, use_container_width=True)
        with row1_col2:
            st.markdown("<b style='color:#212529;'>Tren Ritase Bulanan (2024 vs 2025 vs 2026)</b>", unsafe_allow_html=True)
            df_ritase_trend = df_filtered[df_filtered['YEAR'].isin([2024, 2025, 2026])].groupby(['YEAR', 'MONTH_NUM', 'MONTH_NAME'])['RITASE'].sum().reset_index().sort_values(by='MONTH_NUM')
            df_ritase_trend['YEAR'] = df_ritase_trend['YEAR'].astype(str)
            fig_line = px.line(df_ritase_trend, x='MONTH_NAME', y='RITASE', color='YEAR', markers=True, color_discrete_map={'2024': '#ffccbc', '2025': '#ffb09c', '2026': '#ff5722'})
            fig_line.update_layout(plot_bgcolor='white', paper_bgcolor='white', margin=dict(t=20, b=20, l=20, r=20), xaxis_title=None, yaxis_title="Jumlah Ritase", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_line, use_container_width=True)
            
        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.markdown("<b style='color:#212529;'>Growth Sales (Pertumbuhan % YoY)</b>", unsafe_allow_html=True)
            df_growth = df_filtered[df_filtered['YEAR'].isin([2024, 2025, 2026])].groupby('YEAR')['SALES'].sum().reset_index()
            df_growth['GROWTH_%'] = df_growth['SALES'].pct_change() * 100
            df_growth['GROWTH_%'] = df_growth['GROWTH_%'].fillna(0)
            df_growth['YEAR'] = df_growth['YEAR'].astype(str)
            fig_growth = px.bar(df_growth, x='YEAR', y='GROWTH_%', text=df_growth['GROWTH_%'].apply(lambda x: f"{x:+.1f}%" if x != 0 else "0%"), color_discrete_sequence=['#ff7043'])
            fig_growth.update_layout(plot_bgcolor='white', paper_bgcolor='white', margin=dict(t=20, b=20, l=20, r=20), xaxis_title=None, yaxis_title="Pertumbuhan (%)")
            st.plotly_chart(fig_growth, use_container_width=True)
        with row2_col2:
            st.markdown("<b style='color:#212529;'>Peringkat Sales per Store</b>", unsafe_allow_html=True)
            df_store_sales = df_filtered.groupby('STORE')['SALES'].sum().reset_index().sort_values(by='SALES', ascending=True)
            
            fig_horiz = px.bar(df_store_sales, x='SALES', y='STORE', orientation='h', text_auto=',d')
            fig_horiz.update_traces(marker_color='#ff7043')
            fig_horiz.update_layout(plot_bgcolor='white', paper_bgcolor='white', margin=dict(t=20, b=20, l=20, r=20), xaxis_title="Total Sales (Rp)", yaxis_title=None, xaxis=dict(tickformat=",d"))
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
        st.markdown("<p style='color: #6c757d; font-size: 15px; margin-bottom: 25px;'>Operasional ASG • Real-time Cost Tracking & Fuel Efficiency Control</p>", unsafe_allow_html=True)
        
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
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        total_debit = df_exp_filtered['DEBIT'].sum()
        df_valid_nopol = df_exp_filtered[(df_exp_filtered['NOPOL'].str.upper() != 'TANPA NOPOL') & (df_exp_filtered['NOPOL'].str.strip() != '')]
        unique_nopol_count = df_valid_nopol['NOPOL'].nunique()
        
        exp_kpi1, exp_kpi2 = st.columns(2)
        with exp_kpi1:
            st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Pengeluaran</div><div class="kpi-value">Rp {total_debit:,.0f}</div></div>', unsafe_allow_html=True)
        with exp_kpi2:
            st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Nopol Aktif</div><div class="kpi-value">{unique_nopol_count:,.0f} <span style="font-size:14px; font-weight:400; color:#6c757d;">Unit Armada</span></div></div>', unsafe_allow_html=True)
            
        # ======================================================================
        # ⚠️ KONTROL BATASAN EFISIENSI BBM HPP (KM/Liter - PP Faktor 1.67)
        # ======================================================================
        st.markdown("<div class='section-title'>⚠️ Kontrol Batasan Efisiensi BBM HPP (KM/Liter)</div>", unsafe_allow_html=True)
        
        if not df_master_mbl.empty and not df_harga_live.empty:
            bbm_col_master = [c for c in df_master_mbl.columns if 'BBM' in c or 'BAHAN' in c]
            mobil_col_master = [c for c in df_master_mbl.columns if 'MOBIL' in c or 'ARMADA' in c]
            rasio_col_master = [c for c in df_master_mbl.columns if 'RASIO' in c or 'BATAS' in c]
            
            if bbm_col_master and rasio_col_master:
                df_master_mbl['JENIS_BBM_CLEAN'] = df_master_mbl[bbm_col_master[0]].astype(str).str.strip().str.upper()
                df_master_mbl['RASIO_CLEAN'] = pd.to_numeric(df_master_mbl[rasio_col_master[0]], errors='coerce').fillna(0)
                
                tipe_mobil_title = mobil_col_master[0] if mobil_col_master else df_master_mbl.columns[1]
                
                df_harga_live['TIPE_BBM_CLEAN'] = df_harga_live[df_harga_live.columns[0]].astype(str).str.strip().str.upper()
                df_harga_live['HARGA_CLEAN'] = pd.to_numeric(df_harga_live[df_harga_live.columns[1]], errors='coerce').fillna(0)
                
                df_rules = pd.merge(df_master_mbl, df_harga_live, left_on='JENIS_BBM_CLEAN', right_on='TIPE_BBM_CLEAN', how='left')
                
                df_bbm_only = df_exp_filtered[df_exp_filtered['NAMA'].str.upper().str.contains("BAHAN BAKAR MINYAK HPP", na=False)]
                
                # PROTEKSI UTAMA: Cek jika data transaksi BBM hasil filter kosong, jangan jalankan kalkulasi
                if df_bbm_only.empty:
                    st.info("ℹ️ Belum ada data pemakaian BBM HPP pada filter yang Anda pilih saat ini.")
                else:
                    df_bbm_sum = df_bbm_only.groupby('NOPOL_KEY')['DEBIT'].sum().reset_index().rename(columns={'DEBIT': 'RUPIAH_BBM'})
                    df_km_sum = df_sales_filtered.groupby('NOPOL_KEY')['ALL ONE WAY'].sum().reset_index().rename(columns={'ALL ONE WAY': 'KM_ONE_WAY'})
                    
                    df_merge_calc = pd.merge(df_bbm_sum, df_km_sum, on='NOPOL_KEY', how='outer').fillna(0)
                    df_final_calc = pd.merge(df_merge_calc, df_rules[['NOPOL', 'NOPOL_KEY', tipe_mobil_title, 'JENIS_BBM_CLEAN', 'RASIO_CLEAN', 'HARGA_CLEAN']], on='NOPOL_KEY', how='inner')
                    
                    if not df_final_calc.empty:
                        df_final_calc['JARAK_REAL_PP'] = df_final_calc['KM_ONE_WAY'] * 1.67
                        
                        df_final_calc['ESTIMASI_LITER'] = df_final_calc.apply(
                            lambda r: r['RUPIAH_BBM'] / r['HARGA_CLEAN'] if r['HARGA_CLEAN'] > 0 else 0, axis=1
                        )
                        
                        df_final_calc['RASIO_LAPANGAN_KM_L'] = df_final_calc.apply(
                            lambda r: r['JARAK_REAL_PP'] / r['ESTIMASI_LITER'] if r['ESTIMASI_LITER'] > 0 else 0, axis=1
                        )
                        
                        df_final_calc['STATUS'] = df_final_calc.apply(
                            lambda r: "⚠️ BOROS / OVER BUDGET" if r['RASIO_LAPANGAN_KM_L'] < r['RASIO_CLEAN'] and r['ESTIMASI_LITER'] > 0 else ("✅ AMAN" if r['ESTIMASI_LITER'] > 0 else "Data Tidak Lengkap"), axis=1
                        )
                        
                        list_over = df_final_calc[df_final_calc['STATUS'] == "⚠️ BOROS / OVER BUDGET"]['NOPOL'].tolist()
                        if list_over:
                            st.error(f"⚠️ **PERINGATAN MONITORING BBM:** Armada berikut terdeteksi boros / tidak mencapai target efisiensi jarak rute PP: {', '.join(list_over)}")
                        else:
                            st.success("✅ Seluruh unit kendaraan beroperasi dengan pemakaian BBM yang aman dan efisien sesuai target.")
                            
                        df_view_bbm = df_final_calc[['NOPOL', tipe_mobil_title, 'JENIS_BBM_CLEAN', 'RASIO_CLEAN', 'RUPIAH_BBM', 'KM_ONE_WAY', 'JARAK_REAL_PP', 'ESTIMASI_LITER', 'RASIO_LAPANGAN_KM_L', 'STATUS']].copy()
                        df_view_bbm.columns = ['NO POLISI', 'TIPE MOBIL', 'BAHAN BAKAR', 'TARGET RASIO', 'TOTAL BELANJA BBM', 'KM ONE WAY', 'JARAK REAL PP (x1.67)', 'ESTIMASI LITER', 'RASIO LAPANGAN (KM/L)', 'STATUS']
                        
                        st.dataframe(
                            df_view_bbm.style.format({
                                'TARGET RASIO': '{:,.1f} KM/L',
                                'TOTAL BELANJA BBM': 'Rp {:,.0f}',
                                'KM ONE WAY': '{:,.1f} KM',
                                'JARAK REAL PP (x1.67)': '{:,.1f} KM',
                                'ESTIMASI LITER': '{:,.2f} L',
                                'RASIO LAPANGAN (KM/L)': '{:,.2f} KM/L'
                            }),
                            use_container_width=True, hide_index=True
                        )
                    else:
                        st.info("ℹ️ Tidak ditemukan kecocokan data Nopol kendaraan pada filter ini.")
            else:
                st.warning("Struktur kolom master data kendaraan tidak sesuai ekspektasi.")
        else:
            st.warning("Data Master Kendaraan / Live Harga BBM gagal dimuat.")
            
        with st.sidebar:
            st.markdown("### 📋 Live Monitor Harga BBM")
            if not df_harga_live.empty:
                st.table(df_harga_live.iloc[:, :2].rename(columns={df_harga_live.columns[0]: 'Tipe BBM', df_harga_live.columns[1]: 'Harga/Liter'}))
            st.info("Jika ada perubahan nilai harga bbm resmi, kamu cukup ganti di Google Sheets saja.")
            
        # ======================================================================

        st.markdown("<div class='section-title'>Analisis Grafik Biaya</div>", unsafe_allow_html=True)
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("<b style='color:#212529;'>Tren Pengeluaran Harian per Store</b>", unsafe_allow_html=True)
            df_day_cost = df_exp_filtered.groupby(['TANGGAL', 'STORE'])['DEBIT'].sum().reset_index()
            fig_cost_line = px.line(df_day_cost, x='TANGGAL', y='DEBIT', color='STORE', markers=True)
            fig_cost_line.update_layout(
                plot_bgcolor='white', paper_bgcolor='white', margin=dict(t=20, b=20, l=20, r=20), 
                xaxis_title=None, yaxis_title="Total (Rp)", yaxis=dict(tickformat=",d"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None)
            )
            st.plotly_chart(fig_cost_line, use_container_width=True)
            
        with col_g2:
            st.markdown("<b style='color:#212529;'>Pengeluaran Terbesar per Store</b>", unsafe_allow_html=True)
            df_store_cost = df_exp_filtered.groupby('STORE')['DEBIT'].sum().reset_index().sort_values(by='DEBIT', ascending=True)
            fig_store_bar = px.bar(df_store_cost, x='DEBIT', y='STORE', orientation='h', text_auto=',d')
            fig_store_bar.update_traces(marker_color='#ff7043')
            fig_store_bar.update_layout(
                plot_bgcolor='white', paper_bgcolor='white', margin=dict(t=20, b=20, l=20, r=20), 
                xaxis_title="Total (Rp)", yaxis_title=None, xaxis=dict(tickformat=",d")
            )
            st.plotly_chart(fig_store_bar, use_container_width=True)
            
        st.markdown("<div class='section-title'>Data List Pengeluaran</div>", unsafe_allow_html=True)
        df_list_tabel = df_exp_filtered.groupby(['STORE', 'NAMA', 'NOPOL'])['DEBIT'].sum().reset_index().sort_values(by='DEBIT', ascending=False)
        df_list_tabel.columns = ['STORE', 'NAMA PERSONEL', 'NOMOR POLISI (NOPOL)', 'TOTAL PENGELUARAN']
        
        csv_buffer = df_list_tabel.to_csv(index=False).encode('utf-8')
        df_list_display = df_list_tabel.copy()
        df_list_display['TOTAL PENGELUARAN'] = df_list_display['TOTAL PENGELUARAN'].apply(lambda x: f"Rp {x:,.0f}")
        st.dataframe(df_list_display, use_container_width=True, hide_index=True)
        
        st.download_button(
            label="📥 Download Data List (CSV Excel)",
            data=csv_buffer,
            file_name=f"data_pengeluaran_asg_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

# Footer Aplikasi
st.markdown("<hr style='border: 0.5px solid rgba(235, 94, 40, 0.1);'>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #a0aec0; font-size: 12px;'>Dashboard Multi-Spreadsheet • Built with Streamlit</p>", unsafe_allow_html=True)
