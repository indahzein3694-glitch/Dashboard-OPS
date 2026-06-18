import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. Page Configuration & Theme
st.set_page_config(
    page_title="Sales & Ritase Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Deep Orange & Gen Z CSS Style
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
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

# 2. Data Loading Function (Google Sheets)
@st.cache_data(ttl=600)
def load_data():
    sheet_id = "1Z3sGqENFtjF-gGsRuN4lLUhmGZa5X1AbVx8Ueu-63YQ"
    sheet_name = "LAPORAN"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    
    try:
        df = pd.read_csv(url)
        
        # Clean column names (strip spaces and uppercase)
        df.columns = [c.strip().upper() for c in df.columns]
        
        # Convert TANGGAL to datetime
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce')
        
        # Pembersihan teks dan konversi angka pada kolom SALES
        if 'SALES' in df.columns:
            df['SALES'] = df['SALES'].astype(str).str.replace('Rp', '', regex=False)
            df['SALES'] = df['SALES'].str.replace('.', '', regex=False)
            df['SALES'] = df['SALES'].str.replace(',', '.', regex=False)
            df['SALES'] = df['SALES'].str.strip()
            df['SALES'] = pd.to_numeric(df['SALES'], errors='coerce').fillna(0)
        else:
            df['SALES'] = 0
            
        # Konversi angka untuk RITASE dan YEAR
        df['RITASE'] = pd.to_numeric(df['RITASE'], errors='coerce').fillna(0)
        df['YEAR'] = pd.to_numeric(df['YEAR'], errors='coerce')
        
        # Siasati kolom ALL ONE WAY jika ada perbedaan spasi atau penulisan
        all_one_way_col = [c for c in df.columns if 'ONE WAY' in c]
        if all_one_way_col:
            df['ALL ONE WAY'] = df[all_one_way_col[0]].astype(str).str.replace('.', '', regex=False)
            df['ALL ONE WAY'] = pd.to_numeric(df['ALL ONE WAY'], errors='coerce').fillna(0)
        else:
            df['ALL ONE WAY'] = 0
        
        # Clean string categories
        df['STORE'] = df['STORE'].astype(str).str.strip()
        df['NOPOL'] = df['NOPOL'].astype(str).str.strip()
        
        return df
        
    except Exception as e:
        # Fallback dummy data jika gagal muat dari sheet
        dates = pd.date_range(start="2025-01-01", end="2026-12-31", freq="D")
        dummy_df = pd.DataFrame({
            'TANGGAL': dates,
            'NOPOL': ['B 1234 ABC'] * len(dates),
            'RITASE': [1] * len(dates),
            'STORE': ['Store Contoh'] * len(dates),
            'SALES': [1000000] * len(dates),
            'ALL ONE WAY': [50] * len(dates),
            'YEAR': dates.year,
            'TYPE': ['Carpet'] * len(dates)
        })
        return dummy_df

df_raw = load_data()

# Drop rows with invalid dates
df_cleaned = df_raw.dropna(subset=['TANGGAL']).copy()

# 3. Sidebar Filters
st.sidebar.image("https://img.icons8.com/fluent/96/000000/dashboard.png", width=80)
st.sidebar.markdown("<h2 style='color: #ff5722; font-weight:700;'>Filter Data</h2>", unsafe_allow_html=True)

# Date Filter
min_date = df_cleaned['TANGGAL'].min().to_pydatetime() if not df_cleaned.empty else datetime(2025, 1, 1)
max_date = df_cleaned['TANGGAL'].max().to_pydatetime() if not df_cleaned.empty else datetime(2026, 12, 31)

start_date, end_date = st.sidebar.date_input(
    "Rentang Tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Store Filter
store_options = ["Semua Store"] + sorted(list(df_cleaned['STORE'].unique()))
selected_store = st.sidebar.selectbox("Pilih Store", store_options)

# Filter Processing
df_filtered = df_cleaned[
    (df_cleaned['TANGGAL'] >= pd.to_datetime(start_date)) & 
    (df_cleaned['TANGGAL'] <= pd.to_datetime(end_date))
]

if selected_store != "Semua Store":
    df_filtered = df_filtered[df_filtered['STORE'] == selected_store]

# 4. Header Section
st.markdown("<h1 style='color: #ff5722; font-weight:800; margin-bottom: 5px;'>SALES & RITASE DASHBOARD</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #6c757d; font-size: 15px; margin-bottom: 25px;'>Operasional ASG • Real-time Monitoring & Analysis</p>", unsafe_allow_html=True)

# 5. KPI Metrics Calculation
total_sales = df_filtered['SALES'].sum()
total_all_one_way = df_filtered['ALL ONE WAY'].sum()

# Count Ritase Formula: (countA ritase / total nopol aktif / hari)
total_days = df_filtered['TANGGAL'].nunique()
if total_days > 0:
    count_ritase_total = df_filtered[df_filtered['RITASE'] > 0]['RITASE'].count()
    active_nopol_per_day = df_filtered.groupby('TANGGAL')['NOPOL'].nunique().mean()
    ritase_index = (count_ritase_total / active_nopol_per_day / total_days) if active_nopol_per_day > 0 else 0
else:
    ritase_index = 0

# Render KPI Cards
kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Sales</div>
            <div class="kpi-value">Rp {total_sales:,.0f}</div>
        </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Ritase Index (Avg/Day)</div>
            <div class="kpi-value">{ritase_index:.2f} <span style='font-size:14px; font-weight:400; color:#6c757d;'>rit/truk</span></div>
        </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total All One Way</div>
            <div class="kpi-value">{total_all_one_way:,.0f} <span style='font-size:14px; font-weight:400; color:#6c757d;'>KM</span></div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div class='section-title'>Visualisasi Performa</div>", unsafe_allow_html=True)

# 6. Charts Layout
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.markdown("<b style='color:#212529;'>Perbandingan Sales Tahun 2025 vs 2026</b>", unsafe_allow_html=True)
    df_sales_yr = df_filtered[df_filtered['YEAR'].isin([2025, 2026])].groupby('YEAR')['SALES'].sum().reset_index()
    df_sales_yr['YEAR'] = df_sales_yr['YEAR'].astype(str)
    
    fig_sales = px.bar(
        df_sales_yr, x='YEAR', y='SALES',
        color='YEAR',
        color_discrete_map={'2025': '#ffb09c', '2026': '#ff5722'},
        text_auto='.2s'
    )
    fig_sales.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(t=20, b=20, l=20, r=20), showlegend=False,
        xaxis_title=None, yaxis_title="Total Sales (Rp)"
    )
    st.plotly_chart(fig_sales, use_container_width=True)

with row1_col2:
    st.markdown("<b style='color:#212529;'>Tren Ritase Berkala</b>", unsafe_allow_html=True)
    df_ritase_trend = df_filtered.groupby('TANGGAL')['RITASE'].sum().reset_index()
    
    fig_line = px.line(df_ritase_trend, x='TANGGAL', y='RITASE', markers=True)
    fig_line.update_traces(line_color='#e64a19', marker=dict(size=6, color='#ff5722'))
    fig_line.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(t=20, b=20, l=20, r=20),
        xaxis_title=None, yaxis_title="Jumlah Ritase"
    )
    st.plotly_chart(fig_line, use_container_width=True)

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.markdown("<b style='color:#212529;'>Distribusi Sales per Kategori Produk</b>", unsafe_allow_html=True)
    cat_col = 'TYPE' if 'TYPE' in df_filtered.columns else 'STORE'
    df_cat = df_filtered.groupby(cat_col)['SALES'].sum().reset_index()
    
    fig_donut = px.pie(
        df_cat, names=cat_col, values='SALES',
        hole=0.5,
        color_discrete_sequence=['#ff5722', '#ff7043', '#ff8a65', '#ffab91', '#ffccbc']
    )
    fig_donut.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_donut, use_container_width=True)

with row2_col2:
    st.markdown("<b style='color:#212529;'>Peringkat Sales per Store</b>", unsafe_allow_html=True)
    df_store_sales = df_filtered.groupby('STORE')['SALES'].sum().reset_index().sort_values(by='SALES', ascending=True)
    
    fig_horiz = px.bar(
        df_store_sales, x='SALES', y='STORE',
        orientation='h',
        text_auto='.2s'
    )
    fig_horiz.update_traces(marker_color='#ff7043')
    fig_horiz.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(t=20, b=20, l=20, r=20),
        xaxis_title="Total Sales (Rp)", yaxis_title=None
    )
    st.plotly_chart(fig_horiz, use_container_width=True)

# Footer info
st.markdown("<hr style='border: 0.5px solid rgba(235, 94, 40, 0.1);'>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #a0aec0; font-size: 12px;'>Dashboard Sales & Ritase • Built with Streamlit & Bootstrap styling</p>", unsafe_allow_html=True)
