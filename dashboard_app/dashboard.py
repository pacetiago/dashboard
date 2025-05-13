import os
import pandas as pd
import streamlit as st
import streamlit as st

# ——— 1) Metricas em destaque ———
total_leads   = len(df)
corp_leads    = int(df['is_corporate'].sum())
valid_phones  = int(df['phone_valid'].sum())
avg_score     = df['score'].mean()

st.title("📊 Dashboard de Prospects")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Leads",      total_leads)
col2.metric("Emails Corporativos", corp_leads)
col3.metric("Telefones Válidos",   valid_phones)
col4.metric("Score Médio",         f"{avg_score:.2f}")

st.markdown("---")

# ——— 2) Abas para separar visões ———
tab1, tab2 = st.tabs(["Visão Geral", "Detalhes de Cliente"])

with tab1:
    st.subheader("Distribuição de Score")
    st.bar_chart(df['score'].value_counts().sort_index())

    st.subheader("Proporção de Domínios")
    st.pie_chart(df['is_corporate'].value_counts())

with tab2:
    st.subheader("Filtros")
    # mantêm seus filtros atuais aqui…
    chosen_ddd  = st.selectbox("DDD", ['Todos'] + sorted(df['ddd'].dropna().astype(str).unique()))
    chosen_type = st.selectbox("Tipo de Email", ['Todos','Corporativo','Gratuito'])

    # filtra o DF…
    filtered = df.copy()
    if chosen_ddd  != 'Todos': filtered = filtered[filtered['ddd']==chosen_ddd]
    if chosen_type != 'Todos': filtered = filtered[filtered['is_corporate']==(chosen_type=="Corporativo")]

    st.subheader("Selecione um Cliente")
    client_list = filtered['Empresa'].dropna().unique().tolist()
    cliente = st.selectbox("Empresa", client_list)

    # detalhes num expander
    with st.expander("Ver detalhes completos"):
        info = df[df['Empresa']==cliente].iloc[0]
        st.write(info[['Empresa','Nome','Email','phone_raw','ddd','domain','score']])

    st.subheader("Leads Filtrados")
    st.dataframe(filtered[['Empresa','Nome','Email','phone_raw','ddd','domain','score']])

# ——— 3) Footer limpo — sem logs, apenas rodapé opcional ———
st.markdown("---")
st.caption("Dashboard gerado com Streamlit • atualizado dinamicamente")

# 1) Resolve dinamicamente onde está este arquivo:
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2) Monta o caminho exato para o CSV dentro de dashboard_app/data/
csv_path = os.path.join(BASE_DIR, "data", "prospects.csv")

@st.cache_data
def load_data():
    # 3) Lê o CSV usando o caminho absoluto
    df = pd.read_csv(csv_path)
    # 4) Processa exatamente as mesmas colunas
    df['phone_raw'] = df['Celular'].fillna(df['Telefone']).astype(str)
    df['phone_digits'] = df['phone_raw'].str.replace(r'\D+', '', regex=True)
    def extract_ddd(x):
        if not x or len(x) < 10: return None
        return x[2:4] if x.startswith('55') else x[0:2]
    df['ddd'] = df['phone_digits'].apply(extract_ddd)
    df['domain'] = df['Email'].str.lower().str.split('@').str[-1]
    free = ['gmail.com','hotmail.com','outlook.com','yahoo.com','yahoo.com.br','uol.com.br','globo.com','bol.com.br']
    df['is_corporate'] = ~df['domain'].isin(free)
    df['phone_valid'] = df['phone_digits'].apply(lambda x: len(x) >= 10)
    df['score'] = df['is_corporate'].astype(int) + df['phone_valid'].astype(int)
    return df

# 5) Carrega o DataFrame antes de qualquer uso
df = load_data()
st.write("Colunas disponíveis:", df.columns.tolist())


st.title("Dashboard de Prospects")

# Filtros
st.sidebar.header("Filtros")
ddds = ['Todos'] + sorted(df['ddd'].dropna().astype(str).unique().tolist())
chosen_ddd = st.sidebar.selectbox("DDD", ddds)
types = ['Todos', 'Corporativo', 'Gratuito']
chosen_type = st.sidebar.selectbox("Tipo de Email", types)

filtered = df.copy()
if chosen_ddd != 'Todos':
    filtered = filtered[filtered['ddd'] == chosen_ddd]
if chosen_type != 'Todos':
    filtered = filtered[filtered['is_corporate'] == (chosen_type == 'Corporativo')]

# Seleção de cliente
clients = filtered['Empresa'].dropna().unique().tolist()
if clients:
    client = st.selectbox("Selecione o Cliente", clients)
    info = df[df['Empresa'] == client].iloc[0]
    st.subheader("Detalhes do Cliente")
    st.write({
        'Empresa': info['Empresa'],
        'Nome': info['Nome'],
        'Email': info['Email'],
        'Telefone': info['phone_raw'],
        'DDD': info['ddd'],
        'Domínio': info['domain'],
        'Score': int(info['score'])
    })

# Visão Geral do Filtro
st.subheader("Visão de Leads Filtrados")
st.dataframe(filtered[['Empresa','Nome','Email','phone_raw','ddd','domain','score']].reset_index(drop=True))

st.subheader("Distribuição de Score")
st.bar_chart(filtered['score'].value_counts().sort_index())
