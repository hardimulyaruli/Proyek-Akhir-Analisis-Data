import os

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="E-Commerce EDA Dashboard", layout="wide")

st.title("E-Commerce EDA Dashboard")
st.caption("Visualisasi yang langsung menjawab dua pertanyaan bisnis dari Proyek_Analisis_Data.ipynb")


@st.cache_data
def load_datasets():
    base_paths = [
        os.path.join('..', 'data'),
        os.path.join('..'),
        'data',
        '.',
    ]

    def read_first_available(candidates):
        for base in base_paths:
            for name in candidates:
                path = os.path.join(base, name)
                if os.path.exists(path):
                    return pd.read_csv(path)
        return None

    return {
        'customers': read_first_available(['customers_dataset.csv']),
        'payments': read_first_available(['order_payments_dataset.csv', 'main_data.csv']),
    }


def categorize_installments(value):
    try:
        installments = int(value)
    except Exception:
        return 'Unknown'

    if installments == 1:
        return 'Lunas (1x)'
    if installments > 3:
        return 'Cicilan (>3x)'
    return 'Cicilan 2-3x'


datasets = load_datasets()
payments_df = datasets.get('payments')
customers_df = datasets.get('customers')

if payments_df is None:
    st.error('File order_payments_dataset.csv atau main_data.csv tidak ditemukan. Pastikan file ada di folder data/ atau folder atas.')
else:
    payments_df = payments_df.drop_duplicates().copy()
    if 'payment_value' in payments_df.columns:
        payments_df = payments_df[payments_df['payment_value'] > 0].copy()

    if 'payment_installments' in payments_df.columns:
        payments_df['payment_category'] = payments_df['payment_installments'].apply(categorize_installments)
    else:
        payments_df['payment_category'] = 'Unknown'

    cc_data = payments_df[payments_df['payment_type'] == 'credit_card'].copy() if 'payment_type' in payments_df.columns else pd.DataFrame()
    q1_result = pd.DataFrame()
    avg_lunas = None
    avg_cicilan = None
    diff_pct = None

    if not cc_data.empty:
        q1_result = (
            cc_data.groupby('payment_category', as_index=False)['payment_value']
            .mean()
            .query("payment_category in ['Lunas (1x)', 'Cicilan (>3x)']")
        )
        avg_lunas = q1_result.loc[q1_result['payment_category'] == 'Lunas (1x)', 'payment_value']
        avg_cicilan = q1_result.loc[q1_result['payment_category'] == 'Cicilan (>3x)', 'payment_value']
        if not avg_lunas.empty and not avg_cicilan.empty and avg_lunas.iloc[0] != 0:
            diff_pct = ((avg_cicilan.iloc[0] - avg_lunas.iloc[0]) / avg_lunas.iloc[0]) * 100

    top_states = None
    total_customers_outside_sp = None
    if customers_df is not None and {'customer_unique_id', 'customer_state'}.issubset(customers_df.columns):
        non_sp_customers = customers_df[customers_df['customer_state'] != 'SP'].copy()
        top_states = (
            non_sp_customers.groupby('customer_state')['customer_unique_id']
            .nunique()
            .sort_values(ascending=False)
            .head(5)
            .reset_index()
            .rename(columns={'customer_unique_id': 'unique_customers'})
        )
        total_customers_outside_sp = non_sp_customers['customer_unique_id'].nunique()
    else:
        st.warning('File customers_dataset.csv tidak ditemukan atau tidak memiliki kolom yang dibutuhkan; analisis state tidak tersedia.')

    st.markdown('---')
    overview_left, overview_right = st.columns([1.2, 1])
    with overview_left:
        st.subheader('Ringkasan Pertanyaan Bisnis')
        st.markdown(
            'Dashboard ini hanya memuat visualisasi yang dipakai untuk menjawab pertanyaan bisnis utama: '
            'perbandingan nilai transaksi kartu kredit pada pembayaran lunas (1x) vs cicilan (>3x), serta sebaran pelanggan unik '
            'di luar Sao Paulo.'
        )
    with overview_right:
        if total_customers_outside_sp is not None:
            st.metric('Pelanggan unik di luar SP', f'{total_customers_outside_sp:,}')
        else:
            st.metric('Pelanggan unik di luar SP', 'N/A')

    tab1, tab2 = st.tabs(['Pertanyaan 1', 'Pertanyaan 2'])

    with tab1:
        st.subheader('Bagaimana perbandingan rata-rata nominal transaksi kartu kredit antara pembayaran lunas (1x) dan cicilan (>3x)?')
        st.caption('Analisis hanya menggunakan transaksi kartu kredit dengan 1x cicilan (lunas) vs lebih dari 3x cicilan.')

        q1_metric_1, q1_metric_2, q1_metric_3 = st.columns(3)
        if avg_lunas is not None and not avg_lunas.empty:
            q1_metric_1.metric('Rata-rata Lunas (1x)', f"{avg_lunas.iloc[0]:.2f}")
        else:
            q1_metric_1.metric('Rata-rata Lunas (1x)', 'N/A')

        if avg_cicilan is not None and not avg_cicilan.empty:
            q1_metric_2.metric('Rata-rata Cicilan (>3x)', f"{avg_cicilan.iloc[0]:.2f}")
        else:
            q1_metric_2.metric('Rata-rata Cicilan (>3x)', 'N/A')

        if diff_pct is not None:
            q1_metric_3.metric('Selisih >3x vs 1x', f'{diff_pct:.1f}%')
        else:
            q1_metric_3.metric('Selisih >3x vs 1x', 'N/A')

        if not q1_result.empty:
            q1_fig = px.bar(
                q1_result,
                x='payment_category',
                y='payment_value',
                color='payment_category',
                text='payment_value',
                category_orders={'payment_category': ['Lunas (1x)', 'Cicilan (>3x)']},
                color_discrete_sequence=['#2E86AB', '#F18F01'],
            )
            q1_fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            q1_fig.update_layout(
                xaxis_title='Kategori Pembayaran',
                yaxis_title='Rata-rata Nilai Pembayaran',
                showlegend=False,
            )
            st.plotly_chart(q1_fig, use_container_width=True)
        else:
            st.info('Tidak ada data kartu kredit yang cukup untuk ditampilkan.')

    with tab2:
        st.subheader('State mana saja yang memiliki jumlah pelanggan terbanyak selain Sao Paulo (SP)?')
        st.caption('Visualisasi menampilkan lima state teratas berdasarkan jumlah pelanggan unik di luar SP.')

        if top_states is not None and not top_states.empty:
            top_state_fig = px.bar(
                top_states,
                x='customer_state',
                y='unique_customers',
                color='customer_state',
                text='unique_customers',
                color_discrete_sequence=['#4C78A8', '#F58518', '#54A24B', '#E45756', '#72B7B2'],
            )
            top_state_fig.update_traces(texttemplate='%{text}', textposition='outside')
            top_state_fig.update_layout(
                xaxis_title='State',
                yaxis_title='Jumlah pelanggan unik',
                showlegend=False,
            )
            st.plotly_chart(top_state_fig, use_container_width=True)
            st.dataframe(top_states, use_container_width=True, hide_index=True)
        else:
            st.info('Analisis per-state tidak tersedia.')
