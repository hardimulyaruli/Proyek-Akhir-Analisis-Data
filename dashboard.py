import streamlit as st
import pandas as pd
import plotly.express as px
import os


# Simple Streamlit dashboard implementing notebook EDA
st.set_page_config(page_title="E-Commerce EDA Dashboard", layout="wide")

st.title("E-Commerce EDA Dashboard")
st.caption("Ringkasan interaktif berdasarkan Proyek_Analisis_Data.ipynb")


@st.cache_data
def load_datasets():
    # try common paths inside workspace
    base_paths = [
        os.path.join('..', 'data'),
        os.path.join('..'),
        'data',
        '.'
    ]

    files = {
        'customers': ['customers_dataset.csv'],
        'payments': ['order_payments_dataset.csv', 'main_data.csv'],
        'translation': ['product_category_name_translation.csv']
    }

    loaded = {}
    for key, candidates in files.items():
        df = None
        for base in base_paths:
            for name in candidates:
                path = os.path.join(base, name)
                if os.path.exists(path):
                    try:
                        df = pd.read_csv(path)
                        loaded[key] = df
                        raise StopIteration
                    except StopIteration:
                        break
                    except Exception:
                        df = None
            if df is not None:
                break
        if df is None:
            loaded[key] = None

    return loaded


def categorize_installments(value):
    try:
        value = int(value)
    except Exception:
        return 'Unknown'
    if value == 1:
        return 'Lunas (1x)'
    if value > 3:
        return 'Cicilan > 3x'
    return 'Cicilan 2-3x'


datasets = load_datasets()
payments_df = datasets.get('payments')
customers_df = datasets.get('customers')
translation_df = datasets.get('translation')

if payments_df is None:
    st.error('File order_payments_dataset.csv atau main_data.csv tidak ditemukan. Pastikan file ada di folder data/ atau folder atas.')
else:
    # Basic cleaning similar to notebook
    payments_df = payments_df.drop_duplicates()
    if 'payment_value' in payments_df.columns:
        payments_df = payments_df[payments_df['payment_value'] > 0]

    payments_df['installment_category'] = payments_df.get('payment_installments', 0).apply(categorize_installments)
    available_payment_types = sorted([value for value in payments_df['payment_type'].dropna().unique().tolist()]) if 'payment_type' in payments_df.columns else []
    available_installments = ['Lunas (1x)', 'Cicilan 2-3x', 'Cicilan > 3x']

    with st.sidebar:
        st.header('Filter Interaktif')
        selected_payment_types = st.multiselect(
            'Metode pembayaran',
            options=available_payment_types,
            default=available_payment_types,
        ) if available_payment_types else []
        selected_installment_categories = st.multiselect(
            'Kategori cicilan',
            options=available_installments,
            default=['Lunas (1x)', 'Cicilan > 3x'],
        )

    filtered_payments = payments_df.copy()
    if selected_payment_types:
        filtered_payments = filtered_payments[filtered_payments['payment_type'].isin(selected_payment_types)]
    if selected_installment_categories:
        filtered_payments = filtered_payments[filtered_payments['installment_category'].isin(selected_installment_categories)]

    # Top 3 states outside SP (use customers_df)
    top_3_states = None
    if customers_df is not None and {'customer_unique_id', 'customer_state'}.issubset(set(customers_df.columns)):
        other_states = customers_df[customers_df['customer_state'] != 'SP']
        state_counts = other_states.groupby('customer_state')['customer_unique_id'].nunique().reset_index()
        state_counts = state_counts.rename(columns={'customer_unique_id': 'unique_customers'})
        top_3_states = state_counts.sort_values(by='unique_customers', ascending=False).head(3)
    else:
        st.warning('File customers_dataset.csv tidak ditemukan atau tidak memiliki kolom yang dibutuhkan; analisis per-state tidak tersedia.')

    # Payment type performance
    payment_perf = filtered_payments.groupby('payment_type').agg(
        total_transactions=('order_id', 'count'),
        total_revenue=('payment_value', 'sum')
    ).reset_index().sort_values(by='total_revenue', ascending=False)

    installment_summary = filtered_payments[filtered_payments['installment_category'].isin(['Lunas (1x)', 'Cicilan > 3x'])].groupby('installment_category')['payment_value'].mean().reset_index()

    # Layout
    st.markdown('---')
    c1, c2, c3 = st.columns(3)
    c1.metric('Total Transaksi', f"{filtered_payments['order_id'].nunique():,}")
    if customers_df is not None and 'customer_unique_id' in customers_df.columns:
        c2.metric('Total Pelanggan Unik', f"{customers_df['customer_unique_id'].nunique():,}")
    else:
        c2.metric('Total Pelanggan Unik', 'N/A')
    c3.metric('Metode Pembayaran', f"{filtered_payments['payment_type'].nunique() if 'payment_type' in filtered_payments.columns else 0}")

    tab1, tab2, tab3 = st.tabs(['AOV Cicilan', 'Top 3 States (Luar SP)', 'Payment Type Performance'])

    with tab1:
        st.subheader('Rata-rata Nilai Transaksi: Lunas vs Cicilan > 3x')
        if not installment_summary.empty:
            fig = px.bar(installment_summary, x='installment_category', y='payment_value', color='installment_category', text='payment_value')
            fig.update_layout(yaxis_title='Rata-rata Payment Value', showlegend=False)
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info('Tidak ada data untuk kombinasi filter yang dipilih.')

    with tab2:
        st.subheader('Top 3 Negara Bagian dengan Pelanggan Unik (Luar SP)')
        if top_3_states is not None and not top_3_states.empty:
            fig = px.bar(top_3_states, x='customer_state', y='unique_customers', color='customer_state', text='unique_customers')
            fig.update_traces(texttemplate='%{text}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info('Analisis per-state tidak tersedia.')

    with tab3:
        st.subheader('Performa Tipe Pembayaran')
        if not payment_perf.empty:
            fig = px.bar(payment_perf, x='payment_type', y='total_revenue', text='total_revenue', color='payment_type')
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info('Tidak ada data pembayaran untuk filter yang dipilih.')
