import streamlit as st
import pandas as pd
import sqlite3
import os

# --- Configurações da Página ---
# Será o primeiro comando do Streamlit
st.set_page_config(
    page_title="Análise de Vídeo do YouTube",
    page_icon="📊",
    layout="wide"
)

# --- Constantes ---
DB_NAME = "youtube_stats.db"

# --- Funções de Lógica ---

@st.cache_data(ttl=600) # Faz cache dos dados por 10 minutos (600 segundos)
def carregar_dados():
    """Carrega os dados do banco de dados SQLite."""
    
    # Verifica se o arquivo do banco de dados existe
    if not os.path.exists(DB_NAME):
        st.error(f"Erro: O arquivo de banco de dados '{DB_NAME}' não foi encontrado.")
        st.info("O robô de coleta (GitHub Actions) pode ainda não ter rodado. Aguarde a primeira execução.")
        return pd.DataFrame(columns=["timestamp", "view_count", "like_count", "comment_count"])

    try:
        conn = sqlite3.connect(DB_NAME)
        # Carrega os dados para um DataFrame do Pandas
        df = pd.read_sql_query("SELECT * FROM stats", conn)
        conn.close()
        
        # Converte a coluna 'timestamp' para o formato datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Define o timestamp como o índice do DataFrame
        df.set_index('timestamp', inplace=True)
        
        return df
    except Exception as e:
        st.error(f"Erro ao ler o banco de dados: {e}")
        return pd.DataFrame(columns=["timestamp", "view_count", "like_count", "comment_count"])

def calcular_insights(df):
    """Calcula as 3 análises (insights) com base no DataFrame."""
    if df.empty:
        # Retorna N/A se não houver dados
        return (pd.DataFrame(),) * 3 # Retorna 3 dataframes vazios
    
    # Insight 1: "Velocidade Viral" (Novos Views por Hora)
    # diff() calcula a diferença entre uma linha e a linha anterior
    df_insights = df.copy()
    df_insights['views_por_hora'] = df_insights['view_count'].diff().fillna(0)
    
    # Insight 2: "Taxa de Engajamento" (Likes / Views)
    # Usa os dados *totais* para ter uma taxa estável
    # Multiplica por 100 para ter a porcentagem
    df_insights['taxa_engajamento (%)'] = (df_insights['like_count'] / df_insights['view_count']) * 100
    
    # Insight 3: "Poder de Discussão" (Comentários / Likes)
    df_insights['discussao_por_like'] = df_insights['comment_count'] / df_insights['like_count']
    
    # Limpa dados infinitos (caso haja divisão por zero, ex: 0 likes)
    df_insights.replace([float('inf'), float('-inf')], pd.NA, inplace=True)

    return df_insights

# --- Interface Visual (O Dashboard) ---

st.title("📊 Dashboard de Análise de Vídeo do YouTube")
st.markdown(f"Analisando os dados coletados do arquivo `{DB_NAME}`.")

# Carrega os dados
df_bruto = carregar_dados()
df_insights = calcular_insights(df_bruto)

if df_bruto.empty:
    st.warning("Ainda não há dados para exibir. O coletor precisa rodar pelo menos uma vez.")
else:
    # --- Métricas Principais (Visão Geral) ---
    st.header("📈 Métricas Atuais (Última Coleta)")
    
    # Pega os valores da última linha (coleta mais recente)
    ultima_coleta = df_bruto.iloc[-1]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Visualizações", f"{int(ultima_coleta['view_count']):,}")
    col2.metric("Total de Likes", f"{int(ultima_coleta['like_count']):,}")
    col3.metric("Total de Comentários", f"{int(ultima_coleta['comment_count']):,}")
    
    st.divider() # Linha divisória
    
    # --- Nossas 3 Análises ---
    st.header("💡 Nossos 3 Insights Principais")

    # --- Análise 1 ---
    st.subheader("Análise 1: A 'Velocidade Viral' (Views por Hora)")
    st.markdown("""
    Este gráfico mostra **quantas novas visualizações** o vídeo ganhou *a cada hora*. 
    Ele é melhor que o total de views, pois nos mostra exatamente o **horário de pico** do crescimento.
    """)
    # Usa .iloc[1:] para pular a primeira linha, que não tem 'diff'
    st.bar_chart(df_insights['views_por_hora'].iloc[1:])

    # --- Análise 2 ---
    st.subheader("Análise 2: A 'Taxa de Engajamento' (Likes / Views)")
    st.markdown("""
    Esta é a proporção de **Likes por Visualização**. 
    Uma taxa alta (ex: 10%) sugere que o público adorou. Uma taxa baixa (ex: 1%) sugere o contrário.
    Podemos ver se essa taxa muda conforme o vídeo fica mais popular.
    """)
    st.line_chart(df_insights['taxa_engajamento (%)'])

    # --- Análise 3 ---
    st.subheader("Análise 3: O 'Poder de Discussão' (Comentários / Likes)")
    st.markdown("""
    Esta é a proporção de **Comentários por Like**. 
    Ela nos diz se o vídeo inspira mais **discussão** (alto) ou mais **aprovação silenciosa** (baixo). 
    Vídeos polêmicos ou que fazem perguntas tendem a ter essa taxa mais alta.
    """)
    # Usa .dropna() para remover valores N/A (divisão por zero) do gráfico
    st.line_chart(df_insights['discussao_por_like'].dropna())
    
    st.divider()

    # --- Dados Brutos ---
    st.header("🗃️ Dados Brutos Coletados")
    with st.expander("Clique para ver a tabela de dados completa"):
        # Mostra o dataframe (tabela) interativo
        st.dataframe(df_bruto.sort_index(ascending=False)) # Mostra os mais recentes primeiro

