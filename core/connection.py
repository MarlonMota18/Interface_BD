import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

# Configurações padrão de conexão com o banco de dados (PostgreSQL)
# Podem ser configuradas via variáveis de ambiente para maior segurança
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "f1_database")  # Nome do seu banco de dados F1
DB_USER = os.environ.get("DB_USER", "postgres")    # Seu usuário do PostgreSQL
DB_PASS = os.environ.get("DB_PASS", "postgres")    # Sua senha do PostgreSQL
DB_PORT = os.environ.get("DB_PORT", "5432")

@contextmanager
def get_db_connection():
    """
    Gerenciador de contexto que estabelece a conexão com o PostgreSQL,
    fornece a conexão e garante o fechamento correto após o uso.
    """
    connection = None
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        yield connection
    except Exception as e:
        print(f"Erro ao conectar ou operar no PostgreSQL: {e}")
        if connection:
            connection.rollback()
        raise e
    finally:
        if connection:
            connection.close()

@contextmanager
def get_db_cursor(commit=False):
    """
    Gerenciador de contexto que fornece um cursor dicionário (RealDictCursor).
    Se 'commit' for True, executa o commit ao finalizar com sucesso.
    Retorna os resultados em formato de dicionário Python (ex: row['login'] em vez de row[0]).
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            yield cursor
        if commit:
            conn.commit()
