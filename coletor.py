import os
import sqlite3
import datetime
from googleapiclient.discovery import build

# --- Configurações ---
# ID do vídeo
VIDEO_ID = "i2tFPyw6Iqg" 

# Nome do banco de dados
DB_NAME = "youtube_stats.db"

# A chave de API será lida do "GitHub Secrets"
API_KEY = os.environ.get("YOUTUBE_API_KEY")


def setup_database():
    """Cria a tabela no banco de dados SQLite, se ela não existir."""
    print("Configurando banco de dados...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Cria a tabela
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME NOT NULL,
        view_count INTEGER,
        like_count INTEGER,
        comment_count INTEGER
    );
    """)
    
    conn.commit()
    conn.close()
    print("Banco de dados pronto.")

def fetch_youtube_stats():
    """Busca as estatísticas atuais do vídeo usando a API do YouTube."""
    if not API_KEY:
        raise ValueError("Chave de API do YouTube não encontrada. Configure o Secret 'YOUTUBE_API_KEY'.")

    print(f"Buscando dados para o vídeo ID: {VIDEO_ID}")
    
    # Constrói o "serviço" da API
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    
    # Faz a requisição
    request = youtube.videos().list(
        part="statistics",
        id=VIDEO_ID
    )
    response = request.execute()
    
    if not response.get('items'):
        raise ValueError(f"Não foi possível encontrar o vídeo com ID: {VIDEO_ID}")
        
    # Extrai as estatísticas
    stats = response['items'][0]['statistics']
    
    # Retorna um dicionário limpo
    # Usa .get() para evitar erros se um campo não existir (ex: comments desativados)
    return {
        "views": int(stats.get('viewCount', 0)),
        "likes": int(stats.get('likeCount', 0)),
        "comments": int(stats.get('commentCount', 0))
    }

def save_stats_to_db(stats):
    """Salva as estatísticas coletadas no banco de dados SQLite."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Pega o horário atual
    timestamp = datetime.datetime.now()
    
    # Insere os dados
    cursor.execute("""
    INSERT INTO stats (timestamp, view_count, like_count, comment_count)
    VALUES (?, ?, ?, ?);
    """, (timestamp, stats['views'], stats['likes'], stats['comments']))
    
    conn.commit()
    conn.close()
    print(f"Dados salvos com sucesso: {stats}")

def main():
    """Função principal para orquestrar o script."""
    print("Iniciando script de coleta...")
    try:
        setup_database()
        stats_data = fetch_youtube_stats()
        save_stats_to_db(stats_data)
        print("Coleta concluída com sucesso.")
    except Exception as e:
        print(f"Erro durante a execução: {e}")
        
        raise e 

if __name__ == "__main__":
    main()

