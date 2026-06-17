-- ========================================================
-- PROJETO FINAL - LABORATÓRIO DE BASES DE DADOS (SCC-541)
-- SCRIPT DE CONSULTAS, TRIGGERS, VIEWS E RELATÓRIOS
-- ========================================================

-- ========================================================
-- SEÇÃO 1: TABELAS DO SISTEMA (Estrutura e Auditoria)
-- ========================================================

-- --------------------------------------------------------
-- Tabela: USERS
-- Descrição: Controle de acesso baseado em papéis (RBAC). 
--            id_original é INTEGER e faz referência a chave primária
--            numérica das tabelas de origem (drivers.id ou constructors.id).
-- --------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    userid SERIAL PRIMARY KEY,
    login VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL DEFAULT '123456',
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('Admin', 'Escuderia', 'Piloto')),
    id_original INTEGER -- ID numérico do piloto (drivers.id) ou escuderia (constructors.id)
);

-- --------------------------------------------------------
-- Tabela: USERS_LOG
-- Descrição: Tabela de auditoria para registrar acessos (LOGIN/LOGOUT).
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS users_log (
    logid SERIAL PRIMARY KEY,
    userid INTEGER REFERENCES users(userid) ON DELETE CASCADE,
    action_type VARCHAR(10) CHECK (action_type IN ('LOGIN', 'LOGOUT')),
    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);


-- ========================================================
-- SEÇÃO 2: TRIGGERS PARA CRIAÇÃO AUTOMÁTICA DE USUÁRIOS
-- ========================================================

-- --------------------------------------------------------
-- Trigger e Função: Cadastro de Escuderia
-- Descrição: Ao inserir uma escuderia, cria automaticamente seu 
--            usuário com o sufixo '_c'. Caso exista login duplicado, cancela a operação.
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_insere_usuario_escuderia()
RETURNS TRIGGER AS $$
DECLARE
    v_login VARCHAR(105);
BEGIN
    v_login := NEW.constructor_ref || '_c';
    IF EXISTS (SELECT 1 FROM users WHERE login = v_login) THEN
        RAISE EXCEPTION 'Já existe um usuário com o login %. Operação cancelada.', v_login;
    END IF;
    
    INSERT INTO users (login, password, tipo, id_original)
    VALUES (v_login, crypt(NEW.constructor_ref, gen_salt('bf')), 'Escuderia', NEW.id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_escuderia_user ON constructors;
CREATE TRIGGER trigger_escuderia_user
AFTER INSERT ON constructors
FOR EACH ROW EXECUTE FUNCTION trg_insere_usuario_escuderia();


-- --------------------------------------------------------
-- Trigger e Função: Cadastro de Piloto
-- Descrição: Ao inserir um piloto, cria automaticamente seu 
--            usuário com o sufixo '_d'. Caso exista login duplicado, cancela a operação.
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_insere_usuario_piloto()
RETURNS TRIGGER AS $$
DECLARE
    v_login VARCHAR(105);
BEGIN
    v_login := NEW.driver_ref || '_d';
    IF EXISTS (SELECT 1 FROM users WHERE login = v_login) THEN
        RAISE EXCEPTION 'Já existe um usuário com o login %. Operação cancelada.', v_login;
    END IF;
    
    INSERT INTO users (login, password, tipo, id_original)
    VALUES (v_login, crypt(NEW.driver_ref, gen_salt('bf')), 'Piloto', NEW.id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_piloto_user ON drivers;
CREATE TRIGGER trigger_piloto_user
AFTER INSERT ON drivers
FOR EACH ROW EXECUTE FUNCTION trg_insere_usuario_piloto();


-- --------------------------------------------------------
-- Trigger e Função: Atualização de Escuderia
-- Descrição: Ao modificar o constructor_ref de uma escuderia, atualiza
--            automaticamente seu usuário correspondente na tabela USERS.
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_atualiza_usuario_escuderia()
RETURNS TRIGGER AS $$
DECLARE
    v_login_new VARCHAR(105);
BEGIN
    v_login_new := NEW.constructor_ref || '_c';
    
    IF OLD.constructor_ref <> NEW.constructor_ref THEN
        IF EXISTS (SELECT 1 FROM users WHERE login = v_login_new AND id_original <> NEW.id) THEN
            RAISE EXCEPTION 'Já existe um usuário com o login %. Atualização cancelada.', v_login_new;
        END IF;
        
        UPDATE users
        SET login = v_login_new,
            password = crypt(NEW.constructor_ref, gen_salt('bf'))
        WHERE id_original = NEW.id AND tipo = 'Escuderia';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_escuderia_user_update ON constructors;
CREATE TRIGGER trigger_escuderia_user_update
AFTER UPDATE ON constructors
FOR EACH ROW EXECUTE FUNCTION trg_atualiza_usuario_escuderia();


-- --------------------------------------------------------
-- Trigger e Função: Atualização de Piloto
-- Descrição: Ao modificar o driver_ref de um piloto, atualiza
--            automaticamente seu usuário correspondente na tabela USERS.
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_atualiza_usuario_piloto()
RETURNS TRIGGER AS $$
DECLARE
    v_login_new VARCHAR(105);
BEGIN
    v_login_new := NEW.driver_ref || '_d';
    
    IF OLD.driver_ref <> NEW.driver_ref THEN
        IF EXISTS (SELECT 1 FROM users WHERE login = v_login_new AND id_original <> NEW.id) THEN
            RAISE EXCEPTION 'Já existe um usuário com o login %. Atualização cancelada.', v_login_new;
        END IF;
        
        UPDATE users
        SET login = v_login_new,
            password = crypt(NEW.driver_ref, gen_salt('bf'))
        WHERE id_original = NEW.id AND tipo = 'Piloto';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_piloto_user_update ON drivers;
CREATE TRIGGER trigger_piloto_user_update
AFTER UPDATE ON drivers
FOR EACH ROW EXECUTE FUNCTION trg_atualiza_usuario_piloto();



-- ========================================================
-- SEÇÃO 3: CARGA INICIAL DE DADOS (Seed)
-- ========================================================

-- Inserir administrador padrão
INSERT INTO users (login, password, tipo, id_original)
VALUES ('admin', crypt('admin', gen_salt('bf')), 'Admin', NULL)
ON CONFLICT (login) DO NOTHING;

-- Carga inicial de escuderias existentes para a tabela USERS
INSERT INTO users (login, password, tipo, id_original)
SELECT constructor_ref || '_c', crypt(constructor_ref, gen_salt('bf')), 'Escuderia', id
FROM constructors
ON CONFLICT (login) DO NOTHING;

-- Carga inicial de pilotos existentes para a tabela USERS
INSERT INTO users (login, password, tipo, id_original)
SELECT driver_ref || '_d', crypt(driver_ref, gen_salt('bf')), 'Piloto', id
FROM drivers
ON CONFLICT (login) DO NOTHING;


-- ========================================================
-- SEÇÃO 4: VISÕES (Views) PARA SIMPLIFICAÇÃO E DASHBOARDS
-- ========================================================

-- --------------------------------------------------------
-- View: view_dashboard_admin_escuderias
-- Descrição: Pontuação total das escuderias na temporada mais recente (Dashboard Admin)
-- --------------------------------------------------------
DROP VIEW IF EXISTS view_dashboard_admin_escuderias CASCADE;
CREATE OR REPLACE VIEW view_dashboard_admin_escuderias AS
WITH recent_season AS (
    SELECT r.season_id
    FROM results res
    JOIN races r ON res.race_id = r.id
    ORDER BY r.race_date DESC
    LIMIT 1
)
SELECT
    con.name AS escuderia,
    SUM(res.points) AS total_pontos
FROM results res
JOIN races r ON res.race_id = r.id
JOIN constructors con ON res.constructor_id = con.id
WHERE r.season_id = (SELECT season_id FROM recent_season)
GROUP BY con.id, con.name
 ORDER BY total_pontos DESC;
 
-- --------------------------------------------------------
-- View: view_dashboard_admin_pilotos
-- Descrição: Pontuação total dos pilotos na temporada mais recente (Dashboard Admin)
-- --------------------------------------------------------
DROP VIEW IF EXISTS view_dashboard_admin_pilotos CASCADE;
CREATE OR REPLACE VIEW view_dashboard_admin_pilotos AS
WITH recent_season AS (
    SELECT r.season_id
    FROM results res
    JOIN races r ON res.race_id = r.id
    ORDER BY r.race_date DESC
    LIMIT 1
)
SELECT
    d.given_name || ' ' || d.family_name AS piloto,
    SUM(res.points) AS total_pontos
FROM results res
JOIN races r ON res.race_id = r.id
JOIN drivers d ON res.driver_id = d.id
WHERE r.season_id = (SELECT season_id FROM recent_season)
GROUP BY d.id, d.given_name, d.family_name
 ORDER BY total_pontos DESC;


-- ========================================================
-- SEÇÃO 5: CONSULTAS E FUNÇÕES DO DASHBOARD
-- ========================================================

-- --------------------------------------------------------
-- Função: dashboard_escuderia
-- Parâmetros: p_constructor_id (INTEGER)
-- Descrição: Estatísticas da escuderia para preencher o Dashboard
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION dashboard_escuderia(p_constructor_id INTEGER)
RETURNS TABLE(
    vitorias      BIGINT,
    total_pilotos BIGINT,
    primeiro_ano  INTEGER,
    ultimo_ano    INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) FILTER (WHERE res.position_order = 1)::BIGINT,
        COUNT(DISTINCT res.driver_id)::BIGINT,
        MIN(s.year)::INTEGER,
        MAX(s.year)::INTEGER
    FROM results res
    JOIN races r ON res.race_id = r.id
    JOIN seasons s ON r.season_id = s.id
    WHERE res.constructor_id = p_constructor_id;
END;
$$ LANGUAGE plpgsql;

-- --------------------------------------------------------
-- Função: piloto_anos
-- Parâmetros: p_driver_id (INTEGER)
-- Descrição: Primeiro e último ano de participação de um piloto
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION piloto_anos(p_driver_id INTEGER)
RETURNS TABLE(primeiro_ano INTEGER, ultimo_ano INTEGER) AS $$
BEGIN
    RETURN QUERY
    SELECT MIN(s.year)::INTEGER, MAX(s.year)::INTEGER
    FROM results res
    JOIN races r ON res.race_id = r.id
    JOIN seasons s ON r.season_id = s.id
    WHERE res.driver_id = p_driver_id;
END;
$$ LANGUAGE plpgsql;

-- --------------------------------------------------------
-- Função: piloto_desempenho
-- Parâmetros: p_driver_id (INTEGER)
-- Descrição: Desempenho detalhado do piloto por ano e circuito
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION piloto_desempenho(p_driver_id INTEGER)
RETURNS TABLE(
    ano            INTEGER,
    circuito_nome  TEXT,
    pontos         NUMERIC,
    vitorias       BIGINT,
    corridas       BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.year::INTEGER,
        c.name::TEXT,
        SUM(res.points) AS pontos,
        COUNT(*) FILTER (WHERE res.position_order = 1)::BIGINT AS vitorias,
        COUNT(*)::BIGINT AS corridas
    FROM results res
    JOIN races r ON res.race_id = r.id
    JOIN seasons s ON r.season_id = s.id
    JOIN circuits c ON r.circuit_id = c.id
    WHERE res.driver_id = p_driver_id
    GROUP BY s.year, c.id, c.name
    ORDER BY s.year, c.name;
END;
$$ LANGUAGE plpgsql;


-- ========================================================
-- SEÇÃO 6: AÇÕES OPERACIONAIS (Inserções e Consultas TUI)
-- ========================================================

-- --------------------------------------------------------
-- Função: escuderia_buscar_piloto_sobrenome
-- Parâmetros: p_constructor_id (INTEGER), p_sobrenome (VARCHAR)
-- Descrição: Consulta se piloto já correu pela escuderia usando sobrenome.
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION escuderia_buscar_piloto_sobrenome(
    p_constructor_ref VARCHAR(100),
    p_sobrenome VARCHAR(255)
)
RETURNS TABLE(
    nome_completo TEXT,
    data_nascimento DATE,
    pais VARCHAR(255)
) AS $$
DECLARE
    v_constructor_id INTEGER;
BEGIN
    SELECT id INTO v_constructor_id FROM constructors WHERE constructor_ref = p_constructor_ref;
    
    RETURN QUERY
    SELECT DISTINCT
        (d.given_name || ' ' || d.family_name)::TEXT,
        d.date_of_birth AS data_nascimento,
        c.name AS pais
    FROM results res
    JOIN drivers d ON res.driver_id = d.id
    JOIN countries c ON d.country_id = c.id
    WHERE res.constructor_id = v_constructor_id
      AND d.family_name ILIKE p_sobrenome;
END;
$$ LANGUAGE plpgsql;

-- --------------------------------------------------------
-- Função: escuderia_inserir_piloto
-- Parâmetros: driver_ref, given_name, family_name, date_of_birth, country_id
-- Descrição: Insere piloto validando duplicados por nome/sobrenome.
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION escuderia_inserir_piloto(
    p_driver_ref VARCHAR(100),
    p_given_name VARCHAR(100),
    p_family_name VARCHAR(100),
    p_dob DATE,
    p_country_id INTEGER
)
RETURNS TEXT AS $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM drivers
    WHERE given_name = p_given_name AND family_name = p_family_name;
    
    IF v_count > 0 THEN
        RETURN 'Piloto ' || p_given_name || ' ' || p_family_name || ' já existe. Inserção cancelada.';
    END IF;
    
    INSERT INTO drivers (id, driver_ref, given_name, family_name, date_of_birth, country_id)
    VALUES ((SELECT COALESCE(MAX(id), 0) + 1 FROM drivers), p_driver_ref, p_given_name, p_family_name, p_dob, p_country_id);
    
    RETURN 'Piloto ' || p_given_name || ' ' || p_family_name || ' inserido com sucesso.';
EXCEPTION
    WHEN OTHERS THEN
        RETURN 'Erro ao inserir piloto: ' || SQLERRM;
END;
$$ LANGUAGE plpgsql;


-- ========================================================
-- SEÇÃO 7: IMPLEMENTAÇÃO COMPLETA DOS 7 RELATÓRIOS (Views/Functions)
-- ========================================================

-- --------------------------------------------------------
-- [ADMIN] Relatório 1: Resultados por status (status e contagem)
-- Tipo: View (Sem parâmetros)
-- --------------------------------------------------------
DROP VIEW IF EXISTS view_relatorio_1_status CASCADE;
CREATE OR REPLACE VIEW view_relatorio_1_status AS
SELECT 
    s.status AS status_nome, 
    COUNT(res.id) AS contagem
FROM results res
JOIN status s ON res.status_id = s.id
GROUP BY s.id, s.status
ORDER BY contagem DESC;


-- --------------------------------------------------------
-- [ADMIN] Relatório 2: Aeroportos brasileiros próximos (distância <= 100km)
-- Tipo: Function (Recebe o nome da cidade por parâmetro)
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION relatorio_2_aeroportos(p_cidade VARCHAR)
RETURNS TABLE(
    cidade_pesquisada VARCHAR,
    codigo_iata VARCHAR,
    nome_aeroporto VARCHAR,
    cidade_aeroporto VARCHAR,
    distancia_km NUMERIC,
    tipo_aeroporto VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.name::VARCHAR AS cidade_pesquisada,
        a.iata_code::VARCHAR AS codigo_iata,
        a.name::VARCHAR AS nome_aeroporto,
        city_aeroporto.name::VARCHAR AS cidade_aeroporto,
        ROUND((6371 * acos(
            cos(radians(c.latitude)) * cos(radians(a.latitude_deg)) * 
            cos(radians(a.longitude_deg) - radians(c.longitude)) + 
            sin(radians(c.latitude)) * sin(radians(a.latitude_deg))
        ))::numeric, 2) AS distancia_km,
        at.type::VARCHAR AS tipo_aeroporto
    FROM cities c
    CROSS JOIN airports a
    JOIN airport_types at ON a.airport_type_id = at.id
    JOIN cities city_aeroporto ON a.city_id = city_aeroporto.id
    WHERE c.country_id = (SELECT id FROM countries WHERE name = 'Brazil')
      AND city_aeroporto.country_id = (SELECT id FROM countries WHERE name = 'Brazil')
      AND c.name ILIKE p_cidade
      AND at.type IN ('medium_airport', 'large_airport')
      AND (6371 * acos(
            cos(radians(c.latitude)) * cos(radians(a.latitude_deg)) * 
            cos(radians(a.longitude_deg) - radians(c.longitude)) + 
            sin(radians(c.latitude)) * sin(radians(a.latitude_deg))
        )) <= 100
    ORDER BY distancia_km;
END;
$$ LANGUAGE plpgsql;


-- --------------------------------------------------------
-- [ADMIN] Relatório 3: Hierárquico Escuderias -> Circuitos -> Corridas
-- Tipo: View para Nível 2 e Function para Nível 3
-- --------------------------------------------------------

-- Nível 2: Corridas por circuito com estatísticas de voltas
DROP VIEW IF EXISTS view_relatorio_3_circuitos CASCADE;
CREATE OR REPLACE VIEW view_relatorio_3_circuitos AS
SELECT 
    c.id AS circuit_id,
    c.name AS circuito,
    COUNT(r.id) AS total_corridas,
    MIN(res.laps) AS min_voltas,
    ROUND(AVG(res.laps), 2) AS media_voltas,
    MAX(res.laps) AS max_voltas
FROM races r
JOIN circuits c ON r.circuit_id = c.id
LEFT JOIN results res ON res.race_id = r.id
GROUP BY c.id, c.name;

-- Nível 3: Detalhes por corrida (recebe circuit_id)
CREATE OR REPLACE FUNCTION relatorio_3_corridas_por_circuito(p_circuit_id INTEGER)
RETURNS TABLE(
    corrida VARCHAR,
    voltas_registradas BIGINT,
    total_pilotos BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.race_name::VARCHAR AS corrida,
        SUM(res.laps)::BIGINT AS voltas_registradas,
        COUNT(DISTINCT res.driver_id)::BIGINT AS total_pilotos
    FROM races r
    JOIN results res ON res.race_id = r.id
    WHERE r.circuit_id = p_circuit_id
    GROUP BY r.id, r.race_name
    ORDER BY r.race_name;
END;
$$ LANGUAGE plpgsql;


-- --------------------------------------------------------
-- [ESCUDERIA] Relatório 4: Pilotos da escuderia e vitórias (1º lugar)
-- Tipo: Function (Recebe constructor_id da escuderia logada)
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION relatorio_4_pilotos_vitorias(p_constructor_id INTEGER)
RETURNS TABLE(
    nome_completo TEXT,
    vitorias BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (d.given_name || ' ' || d.family_name)::TEXT AS nome_completo,
        COUNT(res.id) FILTER (WHERE res.position_order = 1)::BIGINT AS vitorias
    FROM results res
    JOIN drivers d ON res.driver_id = d.id
    WHERE res.constructor_id = p_constructor_id
    GROUP BY d.id, d.given_name, d.family_name
    ORDER BY vitorias DESC, nome_completo;
END;
$$ LANGUAGE plpgsql;


-- --------------------------------------------------------
-- [ESCUDERIA] Relatório 5: Resultados por status da escuderia
-- Tipo: Function (Recebe constructor_id da escuderia logada)
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION relatorio_5_status_escuderia(p_constructor_id INTEGER)
RETURNS TABLE(
    status_nome VARCHAR,
    contagem BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.status::VARCHAR AS status_nome,
        COUNT(res.id)::BIGINT AS contagem
    FROM results res
    JOIN status s ON res.status_id = s.id
    WHERE res.constructor_id = p_constructor_id
    GROUP BY s.id, s.status
    ORDER BY contagem DESC;
END;
$$ LANGUAGE plpgsql;


-- --------------------------------------------------------
-- [PILOTO] Relatório 6: Pontos obtidos por ano e corridas
-- Tipo: Function (Recebe driver_id do piloto logado)
-- --------------------------------------------------------
-- Índices para otimizar o Relatório 6
CREATE INDEX IF NOT EXISTS idx_results_driver_points ON results(driver_id, points);
CREATE INDEX IF NOT EXISTS idx_races_season_id ON races(season_id);

CREATE OR REPLACE FUNCTION relatorio_6_pontos_piloto(p_driver_id INTEGER)
RETURNS TABLE(
    ano INTEGER,
    total_pontos NUMERIC,
    corridas_lista TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.year::INTEGER AS ano,
        SUM(res.points)::NUMERIC AS total_pontos,
        STRING_AGG(r.race_name || ' (' || res.points || ' pts)', ', ' ORDER BY r.race_date)::TEXT AS corridas_lista
    FROM results res
    JOIN races r ON res.race_id = r.id
    JOIN seasons s ON r.season_id = s.id
    WHERE res.driver_id = p_driver_id AND res.points > 0
    GROUP BY s.year
    ORDER BY s.year DESC;
END;
$$ LANGUAGE plpgsql;


-- --------------------------------------------------------
-- [PILOTO] Relatório 7: Resultados por status nas corridas
-- Tipo: Function (Recebe driver_id do piloto logado)
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION relatorio_7_status_piloto(p_driver_id INTEGER)
RETURNS TABLE(
    status_nome VARCHAR,
    contagem BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.status::VARCHAR AS status_nome,
        COUNT(res.id)::BIGINT AS contagem
    FROM results res
    JOIN status s ON res.status_id = s.id
    WHERE res.driver_id = p_driver_id
    GROUP BY s.id, s.status
    ORDER BY contagem DESC;
END;
$$ LANGUAGE plpgsql;


-- ========================================================
-- SEÇÃO 8: CRIAÇÃO DE ÍNDICES (Otimizações Obrigatórias)
-- ========================================================

-- Justificativa: Otimiza buscas de pilotos pelo sobrenome na TUI (ILKE/LIKE em family_name).
CREATE INDEX IF NOT EXISTS idx_drivers_family_name ON drivers (family_name);

-- Justificativa: Acelera as junções (JOIN) e agregações de pontos/status em results filtrados por piloto e escuderia.
CREATE INDEX IF NOT EXISTS idx_results_constructor_driver ON results (constructor_id, driver_id);

-- Justificativa: Melhora a performance de junções de tipos de aeroportos na tabela normalizada (Relatório 2).
CREATE INDEX IF NOT EXISTS idx_airports_type_city ON airports (airport_type_id, city_id);
CREATE INDEX IF NOT EXISTS idx_cities_name ON cities (name);


-- ========================================================
-- SEÇÃO 9: ADICIONAIS DO GRUPO (INTEGRAÇÃO ESCUDERIAS)
-- ========================================================

-- Justificativa: Otimiza filtros de busca de resultados por escuderia e posição (ex: vitória).
CREATE INDEX IF NOT EXISTS idx_results_constructor_position ON results(constructor_id, position);

-- Função: get_dashboard_escuderia
-- Parâmetros: p_constructor_ref (VARCHAR)
-- Descrição: Estatísticas gerais da escuderia para preencher o Dashboard a partir da referência de texto.
CREATE OR REPLACE FUNCTION get_dashboard_escuderia(p_constructor_ref VARCHAR)
RETURNS TABLE (
    qtd_vitorias INT,
    qtd_pilotos_diferentes INT,
    primeiro_ano INT,
    ultimo_ano INT
) AS $$
DECLARE
    v_constructor_id INT;
BEGIN
    SELECT id INTO v_constructor_id 
    FROM constructors 
    WHERE constructor_ref = p_constructor_ref;

    RETURN QUERY
    SELECT 
        (SELECT COUNT(*)::INT 
         FROM results 
         WHERE constructor_id = v_constructor_id AND position = '1') AS qtd_vitorias,
        
        (SELECT COUNT(DISTINCT driver_id)::INT 
         FROM results 
         WHERE constructor_id = v_constructor_id) AS qtd_pilotos_diferentes,
        
        (SELECT EXTRACT(YEAR FROM MIN(ra.race_date))::INT 
         FROM results re 
         JOIN races ra ON re.race_id = ra.id 
         WHERE re.constructor_id = v_constructor_id) AS primeiro_ano,
         
        (SELECT EXTRACT(YEAR FROM MAX(ra.race_date))::INT 
         FROM results re 
         JOIN races ra ON re.race_id = ra.id 
         WHERE re.constructor_id = v_constructor_id) AS ultimo_ano;
END;
$$ LANGUAGE plpgsql;

-- Função: get_relatorio4_escuderia
-- Parâmetros: p_constructor_ref (VARCHAR)
-- Descrição: Relatório 4 do PDF - Vitórias de pilotos da escuderia logada por referência.
CREATE OR REPLACE FUNCTION get_relatorio4_escuderia(p_constructor_ref VARCHAR)
RETURNS TABLE (
    nome_piloto VARCHAR,
    qtd_vitorias INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (d.given_name || ' ' || d.family_name)::VARCHAR AS nome_piloto,
        COUNT(*)::INT AS qtd_vitorias
    FROM results r
    JOIN drivers d ON r.driver_id = d.id
    JOIN constructors c ON r.constructor_id = c.id
    WHERE c.constructor_ref = p_constructor_ref
      AND r.position = '1' 
    GROUP BY d.id, d.given_name, d.family_name
    ORDER BY qtd_vitorias DESC;
END;
$$ LANGUAGE plpgsql;

-- Função: get_relatorio5_escuderia
-- Parâmetros: p_constructor_ref (VARCHAR)
-- Descrição: Relatório 5 do PDF - Resultados por status da escuderia logada por referência.
CREATE OR REPLACE FUNCTION get_relatorio5_escuderia(p_constructor_ref VARCHAR)
RETURNS TABLE (
    status VARCHAR,
    contagem INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.status::VARCHAR,
        COUNT(*)::INT AS contagem
    FROM results r
    JOIN status s ON r.status_id = s.id
    JOIN constructors c ON r.constructor_id = c.id
    WHERE c.constructor_ref = p_constructor_ref
    GROUP BY s.id, s.status
    ORDER BY contagem DESC;
END;
$$ LANGUAGE plpgsql;
