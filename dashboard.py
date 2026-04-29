import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Set page configuration
st.set_page_config(
    page_title="E-Commerce Data Dashboard",
    page_icon=":material/bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)


# Title
st.markdown("## :material/bar_chart: E-Commerce Data Dashboard")
st.caption("Dashboard interaktif berdasarkan hasil analisis Proyek_Analisis_Data")

# Sidebar
st.sidebar.title(":material/menu: Navigasi Dashboard")
st.sidebar.markdown("---")

# Load data function
@st.cache_data
def load_data():
    """Load data from main_data.csv"""
    try:
        # Load main_data.csv
        if os.path.exists('main_data.csv'):
            main_df = pd.read_csv('main_data.csv')
            
            # Convert datetime columns if needed
            datetime_columns = ["order_purchase_timestamp", "order_approved_at",
                                "order_delivered_carrier_date", "order_delivered_customer_date",
                                "order_estimated_delivery_date", "review_creation_date", 
                                "review_answer_timestamp"]
            for column in datetime_columns:
                if column in main_df.columns:
                    main_df[column] = pd.to_datetime(main_df[column], errors='coerce')
            
            return main_df
        else:
            st.error("File main_data.csv tidak ditemukan.")
            st.info("Silakan jalankan: python prepare_data.py")
            st.info("Atau letakkan main_data.csv di folder yang sama dengan app.py")
            return None
    
    except Exception as e:
        st.error(f"Error membaca file: {e}")
        return None

# Load data
data = load_data()

if data is not None:
    # Prepare aggregated data for visualizations
    
    # 1. Top Categories
    top_categories_df = data.groupby('product_category_name_english').size().reset_index(name='order_count')
    top_categories_df = top_categories_df.sort_values('order_count', ascending=False).head(10)
    
    # 2. Monthly Orders
    orders_df = data[['order_id', 'order_purchase_timestamp']].drop_duplicates()
    orders_df['order_purchase_timestamp'] = pd.to_datetime(orders_df['order_purchase_timestamp'])
    monthly_orders_df = orders_df.set_index('order_purchase_timestamp').resample('ME').size().reset_index(name='order_count')
    monthly_orders_df.rename(columns={'order_purchase_timestamp': 'order_date'}, inplace=True)
    
    # 3. Customer by State
    customers_state_df = data[['customer_id', 'customer_state']].drop_duplicates()
    bystate_df = customers_state_df.groupby('customer_state').size().reset_index(name='customer_count')
    bystate_df = bystate_df.sort_values('customer_count', ascending=False).head(10)
    
    # Main content
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label=":material/shopping_bag: Total Pesanan",
            value=f"{data['order_id'].nunique():,}",
            delta="Semua waktu"
        )
    
    with col2:
        st.metric(
            label=":material/group: Total Pelanggan",
            value=f"{data['customer_id'].nunique():,}",
            delta="Unik"
        )
    
    with col3:
        st.metric(
            label=":material/local_offer: Kategori Produk",
            value=f"{data['product_category_name_english'].nunique():,}",
            delta="Berbeda"
        )
    
    st.markdown("---")

    summary_col1, summary_col2 = st.columns([1, 1])
    with summary_col1:
        st.markdown("### :material/insights: Kesimpulan Analisis")
        st.write(
            """
            - Kategori produk terlaris pada notebook adalah **bed_bath_table**, **health_beauty**, dan **sports_leisure**.
            - Tren pesanan menunjukkan lonjakan pada **November 2017** yang sangat mungkin terkait **Black Friday**.
            - Pelanggan paling banyak berasal dari **Sao Paulo (SP)**, diikuti **Minas Gerais (MG)** dan **Rio de Janeiro (RJ)**.
            """
        )
    with summary_col2:
        st.markdown("### :material/assignment: Rekomendasi Action Item")
        st.write(
            """
            - Optimasi stok untuk kategori kebutuhan rumah tangga dan perawatan diri.
            - Siapkan kampanye promosi lebih awal sebelum periode Black Friday.
            - Fokus pada wilayah SP untuk efisiensi logistik dan loyalitas pelanggan.
            """
        )
    
    # Tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs([
        ":material/category: Kategori Produk", 
        ":material/monitoring: Tren Bulanan", 
        ":material/public: Distribusi Pelanggan",
        ":material/database: Dataset Info"
    ])
    
    # Tab 1: Top Product Categories
    with tab1:
        st.subheader("10 Kategori Produk Terlaris")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Bar chart
            fig1 = px.bar(
                top_categories_df,
                x='order_count',
                y='product_category_name_english',
                orientation='h',
                title='10 Kategori Produk Terlaris',
                labels={'product_category_name_english': 'Kategori', 'order_count': 'Jumlah Pesanan'},
                color='order_count',
                color_continuous_scale='Viridis',
                text='order_count'
            )
            fig1.update_traces(textposition='auto')
            fig1.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig1, use_container_width=True)
        
        with col1:
            st.markdown("### :material/lightbulb: Insight")
            st.write(f"""
            - Hasil notebook menunjukkan tiga kategori utama adalah **bed_bath_table**, **health_beauty**, dan **sports_leisure**.
            - Kategori tersebut konsisten dengan pola pembelian untuk kebutuhan rumah tangga, perawatan diri, dan gaya hidup.
            - Grafik ini membantu memprioritaskan stok pada kategori dengan permintaan tertinggi.
            """)
    
    # Tab 2: Monthly Trends
    with tab2:
        st.subheader("Tren Jumlah Pesanan per Bulan")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Line chart
            fig2 = px.line(
                monthly_orders_df,
                x='order_date',
                y='order_count',
                title='Tren Penjualan Bulanan',
                labels={'order_date': 'Bulan', 'order_count': 'Jumlah Pesanan'},
                markers=True,
                color_discrete_sequence=['#1f77b4']
            )
            fig2.update_layout(height=450)
            fig2.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig2, use_container_width=True)
        
        with col2:
            st.markdown("### :material/query_stats: Statistik")
            st.metric("Rata-rata Pesanan/Bulan", f"{monthly_orders_df['order_count'].mean():.0f}")
            st.metric("Puncak Pesanan", f"{monthly_orders_df['order_count'].max():,}")
            st.metric("Terendah Pesanan", f"{monthly_orders_df['order_count'].min():,}")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("### :material/trending_up: Insight Tren")
            max_month = monthly_orders_df.loc[monthly_orders_df['order_count'].idxmax(), 'order_date']
            st.write(f"""
            - Analisis notebook menunjukkan pertumbuhan pesanan yang kuat sepanjang periode pengamatan.
            - **Puncak pesanan** terjadi pada bulan {max_month.strftime('%B %Y')} dan selaras dengan lonjakan promo akhir tahun.
            - Periode ini perlu dipersiapkan dengan stok dan kapasitas logistik yang lebih besar.
            """)
        
        with col2:
            st.markdown("### :material/target: Rekomendasi")
            st.write("""
            - Optimalkan persediaan sebelum November.
            - Persiapkan kampanye pemasaran sejak Oktober.
            - Tingkatkan kapasitas fulfillment untuk menjaga kualitas pengiriman.
            """)
    
    # Tab 3: Customer Distribution by State
    with tab3:
        st.subheader("Distribusi Pelanggan per Negara Bagian")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Bar chart
            fig3 = px.bar(
                bystate_df,
                x='customer_count',
                y='customer_state',
                orientation='h',
                title='10 State dengan Jumlah Pelanggan Terbanyak',
                labels={'customer_state': 'State', 'customer_count': 'Jumlah Pelanggan'},
                color='customer_count',
                color_continuous_scale='sunset',
                text='customer_count'
            )
            fig3.update_traces(textposition='auto')
            fig3.update_layout(height=450, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig3, use_container_width=True)
        
        with col1:
            st.markdown("### :material/globe_asia: Insight Geografis")
            sp_percentage = (bystate_df.iloc[0]['customer_count'] / bystate_df['customer_count'].sum()) * 100
            st.write(f"""
            - **São Paulo (SP)** mendominasi dengan {bystate_df.iloc[0]['customer_count']:,} pelanggan ({sp_percentage:.1f}% dari top 10).
            - Tiga state teratas pada notebook adalah **SP**, **MG**, dan **RJ**.
            - Konsentrasi pelanggan di SP menunjukkan pusat aktivitas e-commerce masih sangat terpusat di wilayah tersebut.
            """)
    
    # Tab 4: Dataset Info
    with tab4:
        st.subheader("Informasi Dataset")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### :material/view_agenda: Dimensi Data")
            st.write(f"- **Total Baris:** {data.shape[0]:,}")
            st.write(f"- **Total Kolom:** {data.shape[1]}")
            st.write(f"- **Periode Data:** {data['order_purchase_timestamp'].min().strftime('%B %Y')} - {data['order_purchase_timestamp'].max().strftime('%B %Y')}")
        
        with col2:
            st.markdown("### :material/verified: Kualitas Data")
            missing_pct = (data.isnull().sum().sum() / (data.shape[0] * data.shape[1])) * 100
            st.write(f"- **Missing Values:** {missing_pct:.2f}%")
            st.write(f"- **Memory Usage:** {data.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        
        st.markdown("---")
        st.markdown("### :material/table_chart: Kolom-Kolom Utama")
        col_info = pd.DataFrame({
            'Kolom': data.columns,
            'Tipe Data': data.dtypes,
            'Missing Values': data.isnull().sum()
        })
        st.dataframe(col_info, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; margin-top: 2rem;'>
        <p>Dashboard E-Commerce Data Analysis | Dibuat dengan Streamlit</p>
        <p>Data dibaca dari main_data.csv lokal</p>
    </div>
    """, unsafe_allow_html=True)

else:
    st.error("Gagal memuat data. Silakan periksa file main_data.csv.")
