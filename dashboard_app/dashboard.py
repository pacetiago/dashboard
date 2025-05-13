
import pandas as pd
import streamlit as st

@st.cache_data
def load_data():
    df = pd.read_excel('/mnt/data/Dados Prospect.xlsx')
    df['phone_raw'] = df['Celular'].fillna(df['Telefone']).astype(str)
    df['phone_digits'] = df['phone_raw'].str.replace(r'\D+', '', regex=True)
    def extract_ddd(x):
        if not x or len(x) < 10:
            return None
        if len(x) >= 12 and x.startswith('55'):
            return x[2:4]
        else:
            return x[0:2]
    df['ddd'] = df['phone_digits'].apply(extract_ddd)
    df['domain'] = df['Email'].str.lower().str.split('@').str[-1]
    free = ['gmail.com','hotmail.com','outlook.com','yahoo.com','yahoo.com.br','uol.com.br','globo.com','bol.com.br']
    df['is_corporate'] = ~df['domain'].isin(free)
    df['phone_valid'] = df['phone_digits'].apply(lambda x: len(x) >= 10)
    df['score'] = df['is_corporate'].astype(int) + df['phone_valid'].astype(int)
    return df

df = load_data()
st.title("Dashboard de Prospects")

# Filtros
st.sidebar.header("Filtros")
ddds = ['Todos'] + sorted(df['ddd'].dropna().unique().tolist())
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
