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


# 2. DATA LOADING FUNCTIONS

# --- Fungsi Load Data 1: PERFORMA SALES & RITASE ---
@st.cache_data(ttl=600)
def load_sales_data():
    sheet_id = "1Z3sGqENFtjF-gGsRuN4lLUhmGZa5X1AbVx8Ueu-63YQ"
    sheet_name = "LAPORAN"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip().upper() for c in df.columns]
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce')
        
        if 'SALES' in df.columns:
            df['SALES'] = df['SALES'].astype(str).str.replace('Rp', '', regex=False).str.replace(',', '', regex=False).str.strip()
            df['SALES'] = pd.to_numeric(df['SALES'], errors='coerce').fillna(0)
        else:
            df['SALES'] = 0
            
        df['RITASE'] = pd.to_numeric(df['RITASE'], errors='coerce').fillna(0)
        df['YEAR'] = pd.to_numeric(df['YEAR'], errors='coerce').fillna(df['TANGGAL'].dt.year).fillna(0).astype(int)
        df['MONTH_NAME'] = df['TANGGAL'].dt.strftime('%B')
        df['MONTH_NUM'] = df['TANGGAL'].dt.month
        df['DAY_NUM'] = df['TANGGAL'].dt.day
        
        all_one_way_col = [c for c in df.columns if 'ONE WAY' in c]
        if all_one_way_col:
            df['ALL ONE WAY'] = df[all_one_way_col[0]].astype(str).str.replace(',', '', regex=False)
            df['ALL ONE WAY'] = pd.to_numeric(df['ALL ONE WAY'], errors='coerce').fillna(0)
        else:
            df['ALL ONE WAY'] = 0
            
        df['STORE'] = df['STORE'].fillna('TANPA NAMA').astype(str).str.strip()
        df['NOPOL'] = df['NOPOL'].fillna('TANPA NOPOL').astype(str).str.strip()
        return df
    except Exception as e:
        return pd.DataFrame()

# --- Fungsi Load Data 2: PENGELUARAN (SPREADSHEET BARU) ---
@st.cache_data(ttl=600)
def load_expense_data():
    sheet_id = "1ODK1VYWR6xtFGmpo6CYaLdtzucw2d4uKFDibj8DU3OE"
    sheet_name = "PENGELUARAN"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip().upper() for c in df.columns]
        
        # Format tanggal agar terbaca sempurna
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], dayfirst=True, errors='coerce')
        
        df['YEAR'] = df['TANGGAL'].dt.year
        df['MONTH_NAME'] = df['TANGGAL'].dt.strftime('%B')
        df['DAY_NUM'] = df['TANGGAL'].dt.day
        
        df = df.dropna(subset=['TANGGAL']).copy()
        df['YEAR'] = df['YEAR'].astype(int)
        df['DAY_NUM'] = df['DAY_NUM'].astype(int)
        
        # Bersihkan kolom DEBIT
        if 'DEBIT' in df.columns:
            df['DEBIT'] = df['DEBIT'].astype(str).str.replace('Rp', '', regex=False).str.replace(',', '', regex=False).str.strip()
            df['DEBIT'] = pd.to_numeric(df['DEBIT'], errors='coerce').fillna(0)
        else:
            df['DEBIT'] = 0
            
        df['STORE'] = df['STORE'].fillna('TANPA NAMA').astype(str).str.strip()
        df['NOPOL'] = df['NOPOL'].fillna('TANPA NOPOL').astype(str).str.strip()
        df['NAMA'] = df['NAMA'].fillna('TANPA NAMA').astype(str).str.strip()
        return df
    except Exception as e:
        return pd.DataFrame()


# 3. SIDEBAR NAVIGATION MENU
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
        
        date_options = sorted([int(d) for d in df_cleaned['DAY_NUM'].dropna().unique()])
        selected_dates = st.sidebar.multiselect("Pilih DATE (Tanggal)", options=date_options, default=[])
        
        store_options = sorted([str(s) for s in df_cleaned['STORE'].unique() if str(s).strip() != ''])
        selected_stores = st.sidebar.multiselect("Pilih Store", options=store_options, default=[])
        
        # Filter Process
        df_filtered = df_cleaned.copy()
        if selected_years:
            df_filtered = df_filtered[df_filtered['YEAR'].isin(selected_years)]
        if selected_months:
            df_filtered = df_filtered[df_filtered['MONTH_NAME'].isin(selected_months)]
        if selected_dates:
            df_filtered = df_filtered[df_filtered['DAY_NUM'].isin(selected_dates)]
        if selected_stores:
            df_filtered = df_filtered[df_filtered['STORE'].isin(selected_stores)]
            
        # Header Section
        st.markdown("<h1 style='color: #ff5722; font-weight:800; margin-bottom: 5px;'>SALES & RITASE DASHBOARD</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #6c757d; font-size: 15px; margin-bottom: 25px;'>Operasional ASG • Real-time Monitoring & Analysis</p>", unsafe_allow_html=True)
        
        # KPI Calculation
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
            
            # FORMAT FULL ANGKA
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
            
            # PERBAIKAN GRAFIK SALES: Teks label batangan dan sumbu X diganti nominal full (,d) bukan singkatan SALES/M
            fig_horiz = px.bar(df_store_sales, x='SALES', y='STORE', orientation='h', text_auto=',d')
            fig_horiz.update_traces(marker_color='#ff7043')
            fig_horiz.update_layout(plot_bgcolor='white', paper_bgcolor='white', margin=dict(t=20, b=20, l=20, r=20), xaxis_title="Total Sales (Rp)", yaxis_title=None, xaxis=dict(tickformat=",d"))
            st.plotly_chart(fig_horiz, use_container_width=True)


# ==========================================
# HALAMAN 2: DASHBOARD PENGELUARAN OPERASIONAL
# ==========================================
elif menu_pilihan == "💸 Pengeluaran Operasional":
    df_expense = load_expense_data()
    
    if df_expense.empty:
        st.error("Gagal mengambil data Pengeluaran. Pastikan link Google Sheet Pengeluaran sudah Publik.")
    else:
        # Header Section Pengeluaran
        st.markdown("<h1 style='color: #ff5722; font-weight:800; margin-bottom: 5px;'>PENGELUARAN OPERASIONAL</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #6c757d; font-size: 15px; margin-bottom: 25px;'>Operasional ASG • Real-time Cost Tracking</p>", unsafe_allow_html=True)
        
        # Panel Filter
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
        
        # Proses Filter Data Pengeluaran
        df_exp_filtered = df_expense.copy()
        if sel_exp_years:
            df_exp_filtered = df_exp_filtered[df_exp_filtered['YEAR'].isin(sel_exp_years)]
        if sel_exp_months:
            df_exp_filtered = df_exp_filtered[df_exp_filtered['MONTH_NAME'].isin(sel_exp_months)]
        if sel_exp_dates:
            df_exp_filtered = df_exp_filtered[df_exp_filtered['DAY_NUM'].isin(sel_exp_dates)]
        if sel_exp_stores:
            df_exp_filtered = df_exp_filtered[df_exp_filtered['STORE'].isin(sel_exp_stores)]
        if sel_exp_namas:
            df_exp_filtered = df_exp_filtered[df_exp_filtered['NAMA'].isin(sel_exp_namas)]
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Perhitungan Ringkasan KPI
        total_debit = df_exp_filtered['DEBIT'].sum()
        
        # Hitung Nopol Unik yang Aktif
        df_valid_nopol = df_exp_filtered[(df_exp_filtered['NOPOL'].str.upper() != 'TANPA NOPOL') & (df_exp_filtered['NOPOL'].str.strip() != '')]
        unique_nopol_count = df_valid_nopol['NOPOL'].nunique()
        
        # Render Kartu KPI Pengeluaran
        exp_kpi1, exp_kpi2 = st.columns(2)
        with exp_kpi1:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Total Pengeluaran</div>
                    <div class="kpi-value">Rp {total_debit:,.0f}</div>
                </div>
            """, unsafe_allow_html=True)
        with exp_kpi2:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Total Nopol Aktif</div>
                    <div class="kpi-value">{unique_nopol_count:,.0f} <span style='font-size:14px; font-weight:400; color:#6c757d;'>Unit Armada</span></div>
                </div>
            """, unsafe_allow_html=True)
            
        # Visualisasi Ringkasan Grafik Pengeluaran
        st.markdown("<div class='section-title'>Analisis Grafik Biaya</div>", unsafe_allow_html=True)
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("<b style='color:#212529;'>Tren Pengeluaran Harian</b>", unsafe_allow_html=True)
            df_day_cost = df_exp_filtered.groupby('TANGGAL')['DEBIT'].sum().reset_index()
            fig_cost_line = px.line(df_day_cost, x='TANGGAL', y='DEBIT', markers=True)
            fig_cost_line.update_traces(line_color='#d84315', marker=dict(color='#ff5722'))
            fig_cost_line.update_layout(
                plot_bgcolor='white', 
                paper_bgcolor='white', 
                margin=dict(t=20, b=20, l=20, r=20), 
                xaxis_title=None, 
                yaxis_title="Total (Rp)",
                yaxis=dict(tickformat=",d")
            )
            st.plotly_chart(fig_cost_line, use_container_width=True)
            
        with col_g2:
            st.markdown("<b style='color:#212529;'>Pengeluaran Terbesar per Store</b>", unsafe_allow_html=True)
            df_store_cost = df_exp_filtered.groupby('STORE')['DEBIT'].sum().reset_index().sort_values(by='DEBIT', ascending=True)
            
            # Format label batangan full (,d)
            fig_store_bar = px.bar(df_store_cost, x='DEBIT', y='STORE', orientation='h', text_auto=',d')
            fig_store_bar.update_traces(marker_color='#ff7043')
            fig_store_bar.update_layout(
                plot_bgcolor='white', 
                paper_bgcolor='white', 
                margin=dict(t=20, b=20, l=20, r=20), 
                xaxis_title="Total (Rp)", 
                yaxis_title=None,
                xaxis=dict(tickformat=",d")
            )
            st.plotly_chart(fig_store_bar, use_container_width=True)
            
        # DATA LIST TABULAR
        st.markdown("<div class='section-title'>Data List Pengeluaran</div>", unsafe_allow_html=True)
        
        # Judul kolom tabel bawah: TOTAL PENGELUARAN
        df_list_tabel = df_exp_filtered.groupby(['NAMA', 'NOPOL'])['DEBIT'].sum().reset_index().sort_values(by='DEBIT', ascending=False)
        df_list_tabel.columns = ['NAMA PERSONEL', 'NOMOR POLISI (NOPOL)', 'TOTAL PENGELUARAN']
        
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
st.markdown("<p style='text-align: center; color: #a0aec0; font-size: 12px;'>Dashboard Multi-Spreadsheet • Built with Streamlit & Bootstrap layout style</p>", unsafe_allow_html=True)
