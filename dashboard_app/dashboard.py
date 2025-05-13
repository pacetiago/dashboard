import os
import pandas as pd
import streamlit as st

# ——————— 1) Caminho absoluto para o CSV ———————
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "prospects.csv")

# ——————— 2) Função de carregamento + tratamento ———————
@st.cache_data
def load_data():
    # 1. Lê o CSV
    df = pd.read_csv(CSV_PATH)

    # 2. Renomeia colunas para nomes sem acento/hífen
    df = df.rename(columns={
        'E-mail':      'Email',
        'Razão social': 'Empresa',
        'Telefone':    'Telefone',
        'Celular':     'Celular',
        'Nome':        'Nome'
    })

    # 3. phone_raw: usa Celular ou Telefone
    df['phone_raw'] = df['Celular'].fillna(df['Telefone']).astype(str)

    # 4. phone_digits: só dígitos
    df['phone_digits'] = df['phone_raw'].str.replace(r'\D+', '', regex=True)

    # 5. ddd: extrai DDD (com ou sem '55' na frente)
    def extract_ddd(x):
        if not x or len(x) < 10:
            return None
        return x[2:4] if x.startswith('55') else x[0:2]
    df['ddd'] = df['phone_digits'].apply(extract_ddd)

    # 6. domain: parte após '@'
    df['domain'] = df['Email'].str.lower().str.split('@').str[-1]

    # 7. is_corporate: domínio próprio vs grátis
    FREE = [
        'gmail.com','hotmail.com','outlook.com',
        'yahoo.com','yahoo.com.br','uol.com.br',
        'globo.com','bol.com.br'
    ]
    df['is_corporate'] = ~df['domain'].isin(FREE)

    # 8. phone_valid: ao menos 10 dígitos
    df['phone_valid'] = df['phone_digits'].str.len() >= 10

    # 9. score: soma simples de corporate + valid_phone
    df['score'] = df[['is_corporate','phone_valid']].sum(axis=1)

    return df

# ——————— 3) Carrega dados ———————
df = load_data()

# DEBUG (opcional): mostra colunas pra garantir
# st.write("Colunas disponíveis:", df.columns.tolist())

# ——————— 4) Cálculo de métricas ———————
total_leads  = len(df)
corp_leads   = int(df['is_corporate'].sum())
valid_phones = int(df['phone_valid'].sum())
avg_score    = df['score'].mean()

# ——————— 5) Layout principal ———————
st.set_page_config(layout="wide", page_title="Dashboard de Prospects")

st.title("📊 Dashboard de Prospects")

# ——— Métricas em destaque ———
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total de Leads",       total_leads)
c2.metric("Emails Corporativos",  corp_leads)
c3.metric("Telefones Válidos",    valid_phones)
c4.metric("Score Médio",          f"{avg_score:.2f}")

st.markdown("---")

# ——— Abas: Visão Geral vs Detalhes ———
tab1, tab2 = st.tabs(["Visão Geral", "Detalhes de Cliente"])

with tab1:
    st.subheader("Distribuição de Score")
    st.bar_chart(df['score'].value_counts().sort_index())

    st.subheader("Proporção de Domínios")
    st.pie_chart(df['is_corporate'].value_counts())

with tab2:
    st.subheader("Filtros de Segmentação")
    chosen_ddd  = st.selectbox("DDD", ['Todos'] + sorted(df['ddd'].dropna().astype(str).unique()))
    chosen_type = st.selectbox("Tipo de Email", ['Todos', 'Corporativo', 'Gratuito'])

    # Aplica filtros
    filtered = df.copy()
    if chosen_ddd  != 'Todos':
        filtered = filtered[filtered['ddd'] == chosen_ddd]
    if chosen_type != 'Todos':
        filtered = filtered[filtered['is_corporate'] == (chosen_type == "Corporativo")]

    st.subheader("Selecione um Cliente")
    client_list = filtered['Empresa'].dropna().unique().tolist()
    if client_list:
        cliente = st.selectbox("Empresa", client_list)

        # Expander com detalhes
        with st.expander("Ver detalhes completos"):
            info = df[df['Empresa'] == cliente].iloc[0]
            st.write({
                'Empresa':   info['Empresa'],
                'Nome':      info['Nome'],
                'Email':     info['Email'],
                'Telefone':  info['phone_raw'],
                'DDD':       info['ddd'],
                'Domínio':   info['domain'],
                'Score':     int(info['score'])
            })

    st.subheader("Leads Filtrados")
    st.dataframe(filtered[['Empresa','Nome','Email','phone_raw','ddd','domain','score']])

st.markdown("---")
st.caption("Gerado com Streamlit • Atualizado dinamicamente")
