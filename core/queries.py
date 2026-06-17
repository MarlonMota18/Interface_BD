from core.connection import get_db_cursor

# ========================================================
# CONSULTAS DO DASHBOARD DO ADMINISTRADOR
# ========================================================

def get_admin_dashboard_counts():
    """
    Retorna o total de pilotos, escuderias e temporadas cadastradas.
    """
    query = """
        SELECT
            (SELECT COUNT(*) FROM drivers)     AS total_pilotos,
            (SELECT COUNT(*) FROM constructors) AS total_escuderias,
            (SELECT COUNT(*) FROM seasons)      AS total_temporadas;
    """
    with get_db_cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchone()

def get_admin_recent_races():
    """
    Obtém todas as corridas da última temporada com circuito, data, hora e total de voltas.
    """
    query = """
        WITH recent_season AS (
            SELECT r.season_id
            FROM results res
            JOIN races r ON res.race_id = r.id
            ORDER BY r.race_date DESC
            LIMIT 1
        )
        SELECT
            r.race_name AS corrida,
            c.name      AS circuito,
            r.race_date AS data,
            r.race_time AS horario,
            (SELECT MAX(laps) FROM results WHERE race_id = r.id) AS total_voltas
        FROM races r
        JOIN circuits c ON r.circuit_id = c.id
        WHERE r.season_id = (SELECT season_id FROM recent_season)
        ORDER BY r.race_date;
    """
    with get_db_cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()

def get_admin_escuderias_points():
    """
    Usa a view view_dashboard_admin_escuderias para listar a pontuação do último ano.
    """
    query = "SELECT escuderia, total_pontos FROM view_dashboard_admin_escuderias LIMIT 10;"
    with get_db_cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()

def get_admin_pilotos_points():
    """
    Usa a view view_dashboard_admin_pilotos para listar a pontuação dos pilotos no último ano.
    """
    query = "SELECT piloto, total_pontos FROM view_dashboard_admin_pilotos LIMIT 10;"
    with get_db_cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


# ========================================================
# FUNÇÕES E CONSULTAS DO DASHBOARD DE ESCUDERIA/PILOTO
# ========================================================

def get_escuderia_dashboard(constructor_ref: str):
    """
    Chama a função get_dashboard_escuderia(p_constructor_ref) no banco.
    """
    query = "SELECT * FROM get_dashboard_escuderia(%s);"
    with get_db_cursor() as cursor:
        cursor.execute(query, (constructor_ref,))
        return cursor.fetchone()

def get_piloto_anos(driver_id: int):
    """
    Chama a função piloto_anos(p_driver_id) no banco.
    """
    query = "SELECT * FROM piloto_anos(%s);"
    with get_db_cursor() as cursor:
        cursor.execute(query, (driver_id,))
        return cursor.fetchone()

def get_piloto_desempenho(driver_id: int):
    """
    Chama a função piloto_desempenho(p_driver_id) no banco.
    """
    query = "SELECT * FROM piloto_desempenho(%s);"
    with get_db_cursor() as cursor:
        cursor.execute(query, (driver_id,))
        return cursor.fetchall()


# ========================================================
# MÉTODOS DE CADASTROS E BUSCAS OPERACIONAIS
# ========================================================

def buscar_piloto_por_sobrenome(constructor_ref: str, sobrenome: str):
    """
    Chama a função de busca por sobrenome para a escuderia logada, usando sua referência de texto.
    """
    query = "SELECT * FROM escuderia_buscar_piloto_sobrenome(%s, %s);"
    with get_db_cursor() as cursor:
        cursor.execute(query, (constructor_ref, sobrenome))
        return cursor.fetchall()

def cadastrar_novo_piloto(driver_ref: str, given_name: str, family_name: str, dob: str, country_id: int) -> str:
    """
    Chama a procedure escuderia_inserir_piloto no banco. (Versão original com country_id)
    """
    query = "SELECT escuderia_inserir_piloto(%s, %s, %s, %s, %s);"
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, (driver_ref, given_name, family_name, dob, country_id))
            result = cursor.fetchone()
            return result['escuderia_inserir_piloto'] if result else "Erro na execução."
    except Exception as e:
        return f"Erro no banco de dados: {e}"

def cadastrar_novo_piloto_por_nacionalidade(driver_id: str, givenName: str, familyName: str, nationality: str, dob: str) -> str:
    """
    Resolve a nacionalidade para o country_id e chama a procedure escuderia_inserir_piloto no banco.
    """
    query_country = "SELECT id FROM countries WHERE nationality ILIKE %s LIMIT 1;"
    query_insert = "SELECT escuderia_inserir_piloto(%s, %s, %s, %s, %s);"
    try:
        with get_db_cursor(commit=True) as cursor:
            # 1. Resolve a nacionalidade
            cursor.execute(query_country, (nationality,))
            row = cursor.fetchone()
            if not row:
                return f"Nacionalidade '{nationality}' não encontrada."
            country_id = row['id']
            
            # 2. Insere
            cursor.execute(query_insert, (driver_id, givenName, familyName, dob, country_id))
            result = cursor.fetchone()
            return result['escuderia_inserir_piloto'] if result else "Erro na execução."
    except Exception as e:
        return f"Erro no banco de dados: {e}"



# ========================================================
# MÉTODOS DE RELATÓRIOS DA TELA 3
# ========================================================

def get_relatorio_1_status():
    """
    [ADMIN] Relatório 1: Resultados gerais por status.
    """
    query = "SELECT status_nome, contagem FROM view_relatorio_1_status;"
    with get_db_cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()

def get_relatorio_2_aeroportos(cidade: str):
    """
    [ADMIN] Relatório 2: Aeroportos brasileiros próximos a cidade pesquisada.
    """
    query = "SELECT * FROM relatorio_2_aeroportos(%s);"
    with get_db_cursor() as cursor:
        cursor.execute(query, (cidade,))
        return cursor.fetchall()

def get_relatorio_3_circuitos():
    """
    [ADMIN] Relatório 3 - Nível 2: Lista os circuitos e estatísticas de voltas.
    """
    query = "SELECT * FROM view_relatorio_3_circuitos;"
    with get_db_cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()

def get_relatorio_3_corridas(circuit_id: int):
    """
    [ADMIN] Relatório 3 - Nível 3: Detalhes das corridas por circuito.
    """
    query = "SELECT * FROM relatorio_3_corridas_por_circuito(%s);"
    with get_db_cursor() as cursor:
        cursor.execute(query, (circuit_id,))
        return cursor.fetchall()

def get_relatorio_4_pilotos_vitorias(constructor_ref: str):
    """
    [ESCUDERIA] Relatório 4: Pilotos da escuderia logada e vitórias, filtrando por ref.
    """
    query = "SELECT * FROM get_relatorio4_escuderia(%s);"
    with get_db_cursor() as cursor:
        cursor.execute(query, (constructor_ref,))
        return cursor.fetchall()

def get_relatorio_5_status_escuderia(constructor_ref: str):
    """
    [ESCUDERIA] Relatório 5: Resultados por status da escuderia logada, filtrando por ref.
    """
    query = "SELECT * FROM get_relatorio5_escuderia(%s);"
    with get_db_cursor() as cursor:
        cursor.execute(query, (constructor_ref,))
        return cursor.fetchall()

def get_relatorio_6_pontos_piloto(driver_id: int):
    """
    [PILOTO] Relatório 6: Pontos por ano do piloto logado.
    """
    query = "SELECT * FROM relatorio_6_pontos_piloto(%s);"
    with get_db_cursor() as cursor:
        cursor.execute(query, (driver_id,))
        return cursor.fetchall()

def get_relatorio_7_status_piloto(driver_id: int):
    """
    [PILOTO] Relatório 7: Resultados por status do piloto logado.
    """
    query = "SELECT * FROM relatorio_7_status_piloto(%s);"
    with get_db_cursor() as cursor:
        cursor.execute(query, (driver_id,))
        return cursor.fetchall()


def get_countries():
    """
    Retorna a lista de países cadastrados com suas nacionalidades.
    """
    query = "SELECT id, name, nationality FROM countries WHERE nationality IS NOT NULL ORDER BY nationality;"
    with get_db_cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


def cadastrar_escuderia(constructor_ref: str, name: str, nationality: str, wikipedia_url: str) -> str:
    """
    Cadastra uma nova escuderia na tabela CONSTRUCTORS resolvendo a nacionalidade.
    A trigger correspondente insere automaticamente o usuário em USERS.
    """
    query_country = "SELECT id FROM countries WHERE nationality ILIKE %s LIMIT 1;"
    query_insert = """
        INSERT INTO constructors (id, constructor_ref, name, country_id, wikipedia_url)
        VALUES ((SELECT COALESCE(MAX(id), 0) + 1 FROM constructors), %s, %s, %s, %s)
        RETURNING name;
    """
    try:
        with get_db_cursor(commit=True) as cursor:
            # Resolve a nacionalidade
            cursor.execute(query_country, (nationality,))
            row = cursor.fetchone()
            if not row:
                return f"Nacionalidade '{nationality}' não encontrada."
            country_id = row['id']
            
            cursor.execute(query_insert, (constructor_ref, name, country_id, wikipedia_url or None))
            result = cursor.fetchone()
            if result:
                return f"Escuderia '{result['name']}' cadastrada com sucesso!"
            return "Erro ao cadastrar escuderia."
    except Exception as e:
        return f"Erro ao cadastrar escuderia: {str(e)}"


def get_escuderia_info(constructor_id: int):
    """
    Retorna o nome oficial da escuderia e o total de pilotos diferentes associados a ela.
    """
    query = """
        SELECT 
            name, 
            (SELECT COUNT(DISTINCT driver_id) FROM results WHERE constructor_id = id) AS total_pilotos
        FROM constructors 
        WHERE id = %s;
    """
    with get_db_cursor() as cursor:
        cursor.execute(query, (constructor_id,))
        return cursor.fetchone()


def get_piloto_info(driver_id: int):
    """
    Retorna o nome completo do piloto e o nome da escuderia mais recente pela qual ele correu.
    """
    query = """
        SELECT 
            d.given_name || ' ' || d.family_name AS nome_completo,
            COALESCE(
                (SELECT c.name 
                 FROM results res
                 JOIN races r ON res.race_id = r.id
                 JOIN constructors c ON res.constructor_id = c.id
                 WHERE res.driver_id = d.id
                 ORDER BY r.race_date DESC
                 LIMIT 1), 
                'Sem Escuderia'
            ) AS escuderia_nome
        FROM drivers d
        WHERE d.id = %s;
    """
    with get_db_cursor() as cursor:
        cursor.execute(query, (driver_id,))
        return cursor.fetchone()


