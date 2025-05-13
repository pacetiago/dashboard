import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ——————— 1) Caminho absoluto para o CSV ———————
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "prospects.csv")

# ——————— 2) Função de carregamento + tratamento ———————
@st.cache_data
def load_data():
    df = pd.read_csv(CSV_PATH)

    # Renomeia para colunas sem acentos/hífen
    df = df.rename(columns={
        'E-mail':       'Email',
        'Razão social': 'Empresa',
        'Telefone':     'Telefone',
        'Celular':      'Celular',
        'Nome':         'Nome'
    })

    df['phone_raw']    = df['Celular'].fillna(df['Telefone']).astype(str)
    df['phone_digits'] = df['phone_raw'].str.replace(r'\D+', '', regex=True)

    def extract_ddd(x):
        if not x or len(x) < 10:
            return None
        return x[2:4] if x.startswith('55') else x[0:2]

    df['ddd']          = df['phone_digits'].apply(extract_ddd)
    df['domain']       = df['Email'].str.lower().str.split('@').str[-1]

    FREE = [
        'gmail.com','hotmail.com','outlook.com',
        'yahoo.com','yahoo.com.br','uol.com.br',
        'globo.com','bol.com.br'
    ]
    df['is_corporate'] = ~df['domain'].isin(FREE)
    df['phone_valid']  = df['phone_digits'].str.len() >= 10
    df['score']        = df[['is_corporate','phone_valid']].sum(axis=1)

    return df

# ——————— 3) Carrega dados ———————
df = load_data()

# ——————— 4) Cálculo de métricas ———————
total_leads  = len(df)
corp_leads   = int(df['is_corporate'].sum())
valid_phones = int(df['phone_valid'].sum())
avg_score    = df['score'].mean()

# ——————— 5) Configurações da página e título ———————
st.set_page_config(layout="wide", page_title="Dashboard de Prospects")
st.title("📊 Dashboard de Prospects")

# ——— Métricas em destaque ———
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total de Leads",       total_leads)
c2.metric("Emails Corporativos",  corp_leads)
c3.metric("Telefones Válidos",    valid_phones)
c4.metric("Score Médio",          f"{avg_score:.2f}")

st.markdown("---")

# ——— Abas: Visão Geral vs Detalhes de Cliente ———
tab1, tab2 = st.tabs(["Visão Geral", "Detalhes de Cliente"])

with tab1:
    st.subheader("Distribuição de Score")
    st.bar_chart(df['score'].value_counts().sort_index())

    st.subheader("Proporção de Domínios")
    # Matplotlib pie chart
    counts = df['is_corporate'].value_counts()
    labels = ['Corporativo' if x else 'Gratuito' for x in counts.index]
    fig, ax = plt.subplots()
    ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    ax.set_title("Emails Corporativos vs. Gratuitos")
    st.pyplot(fig)

with tab2:
    st.subheader("Filtros de Segmentação")
    chosen_ddd  = st.selectbox("DDD", ['Todos'] + sorted(df['ddd'].dropna().astype(str).unique()))
    chosen_type = st.selectbox("Tipo de Email", ['Todos', 'Corporativo', 'Gratuito'])

    filtered = df.copy()
    if chosen_ddd  != 'Todos':
        filtered = filtered[filtered['ddd'] == chosen_ddd]
    if chosen_type != 'Todos':
        filtered = filtered[filtered['is_corporate'] == (chosen_type == "Corporativo")]

    st.subheader("Selecione um Cliente")
    client_list = filtered['Empresa'].dropna().unique().tolist()
    if client_list:
        cliente = st.selectbox("Empresa", client_list)
        with st.expander("Ver detalhes completos"):
            info = df[df['Empresa'] == cliente].iloc[0]
            st.write({
                'Empresa':  info['Empresa'],
                'Nome':     info['Nome'],
                'Email':    info['Email'],
                'Telefone': info['phone_raw'],
                'DDD':      info['ddd'],
                'Domínio':  info['domain'],
                'Score':    int(info['score'])
            })

    st.subheader("Leads Filtrados")
    st.dataframe(filtered[['Empresa','Nome','Email','phone_raw','ddd','domain','score']])

st.markdown("---")
st.caption("Gerado com Streamlit • Atualizado dinamicamente")
