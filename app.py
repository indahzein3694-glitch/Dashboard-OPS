import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi Halaman Dashboard
st.set_page_config(
    page_title="Dashboard Master Kendaraan ASG",
    page_icon="🚚",
    layout="wide"
)

# 2. Ambil Data dari Google Sheets (Menggunakan Link yang Anda Berikan)
# Bagian /edit... diubah menjadi /export?format=csv untuk akses langsung via Python
SHEET_URL = "https://docs.google.com/spreadsheets/d/1TKznhfQwdPSdMu4dPxoMXis-3jR9QRCAqLAUzBAftpk/export?format=csv"

@st.cache_data
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        # Membersihkan nama kolom dari spasi berlebih jika ada
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Gagal memuat data dari Google Sheets: {e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- HEADER DASHBOARD ---
    st.title("🚚 Dashboard Analisis Master Kendaraan")
    st.markdown("Aplikasi monitoring dan visualisasi data operasional armada secara real-time.")
    st.divider()

    # --- SIDEBAR & FILTER ---
    st.sidebar.header("Filter Data")
    
    # Filter Toko / Store
    toko_list = ["Semua Toko"] + list(df['Toko'].dropna().unique())
    selected_toko = st.sidebar.selectbox("Pilih Lokasi Toko:", toko_list)
    
    # Filter Jenis Mobil
    jenis_mobil_list = ["Semua Jenis"] + list(df['Jenis Mobil'].dropna().unique())
    selected_mobil = st.sidebar.selectbox("Pilih Jenis Mobil:", jenis_mobil_list)

    # Menerapkan filter pada dataframe
    df_filtered = df.copy()
    if selected_toko != "Semua Toko":
        df_filtered = df_filtered[df_filtered['Toko'] == selected_toko]
    if selected_mobil != "Semua Jenis":
        df_filtered = df_filtered[df_filtered['Jenis Mobil'] == selected_mobil]

    # --- BARISAN METRIK UTAMA (KPI CARDS) ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Armada / Kendaraan", value=len(df_filtered))
    with col2:
        # Menghitung rata-rata rasio konsumsi BBM standar
        avg_rasio = df_filtered['Rasio Standar Km/Liter'].mean()
        st.metric(label="Rata-rata Rasio BBM (Km/Liter)", value=f"{avg_rasio:.2f}" if not pd.isna(avg_rasio) else "0")
    with col3:
        # Jumlah variasi toko yang terdaftar pada filter aktif
        total_toko = df_filtered['Toko'].nunique()
        st.metric(label="Jumlah Toko Tercover", value=total_toko)

    st.divider()

    # --- VISUALISASI GRAFIK (LAYOUT 2 KOLOM) ---
    graph_col1, graph_col2 = st.columns(2)

    with graph_col1:
        st.subheader("📊 Distribusi Jenis BBM")
        if 'Jenis BBM' in df_filtered.columns and not df_filtered.empty:
            fig_bbm = px.pie(
                df_filtered, 
                names='Jenis BBM', 
                title="Persentase Penggunaan Jenis BBM",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_bbm, use_container_width=True)
        else:
            st.info("Data BBM tidak tersedia.")

    with graph_col2:
        st.subheader("📈 Rata-rata Rasio BBM per Jenis Mobil")
        if 'Jenis Mobil' in df_filtered.columns and 'Rasio Standar Km/Liter' in df_filtered.columns:
            # Grouping data berdasarkan jenis mobil
            df_rasio = df_filtered.groupby('Jenis Mobil')['Rasio Standar Km/Liter'].mean().reset_index()
            fig_rasio = px.bar(
                df_rasio,
                x='Jenis Mobil',
                y='Rasio Standar Km/Liter',
                title="Rasio Standar Km/Liter Berdasarkan Tipe Mobil",
                labels={'Rasio Standar Km/Liter': 'Km / Liter'},
                color='Jenis Mobil',
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            st.plotly_chart(fig_rasio, use_container_width=True)
        else:
            st.info("Data Rasio Mobil tidak dapat dikalkulasi.")

    st.divider()

    # --- TABEL DATA INTERAKTIF ---
    st.subheader("📋 Detail Data Kendaraan Terfilter")
    st.dataframe(df_filtered, use_container_width=True)

else:
    st.warning("Data kosong atau spreadsheet tidak dapat diakses. Pastikan pengaturan berbagi (sharing) link Google Sheets Anda sudah diatur ke 'Siapa saja yang memiliki link dapat melihat' (Anyone with the link can view).")
