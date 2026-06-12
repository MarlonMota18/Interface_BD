-- INÍCIO FUNÇÃO ESCUDERIAS DASHBOARD

/* CONCEITO: Procedimentos e Funções.
JUSTIFICATIVA: A utilização de uma função em PL/pgSQL permite encapsular múltiplas consultas
de agregação numa única chamada à base de dados. Isto reduz o tráfego de rede e otimiza o carregamento do Dashboard,
retornando os quatro indicadores fundamentais da escuderia de uma só vez.
*/
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
    -- Busca o ID numérico da escuderia com base no ref do utilizador autenticado
    SELECT id INTO v_constructor_id 
    FROM constructors 
    WHERE constructor_ref = p_constructor_ref;

    RETURN QUERY
    SELECT 
        -- 1. Quantidade de vitórias
        (SELECT COUNT(*)::INT 
         FROM results 
         WHERE constructor_id = v_constructor_id AND position = '1') AS qtd_vitorias,
        
        -- 2. Quantidade de pilotos diferentes
        (SELECT COUNT(DISTINCT driver_id)::INT 
         FROM results 
         WHERE constructor_id = v_constructor_id) AS qtd_pilotos_diferentes,
        
        -- 3. Primeiro ano na base 
        (SELECT EXTRACT(YEAR FROM MIN(ra.race_date))::INT 
         FROM results re 
         JOIN races ra ON re.race_id = ra.id 
         WHERE re.constructor_id = v_constructor_id) AS primeiro_ano,
         
        -- 4. Último ano na base 
        (SELECT EXTRACT(YEAR FROM MAX(ra.race_date))::INT 
         FROM results re 
         JOIN races ra ON re.race_id = ra.id 
         WHERE re.constructor_id = v_constructor_id) AS ultimo_ano;
END;
$$ LANGUAGE plpgsql;

-- Função usada para teste: SELECT * FROM get_dashboard_escuderia('mclaren');

-- FIM FUNÇÃO ESCUDERIAS DASHBOARD


-- SQL RELATÓRIO 4 (ESCUDERIAS)

/*
JUSTIFICATIVA ÍNDICE: Este índice composto (constructor_id, position) foi criado na tabela RESULTS para otimizar os filtros do Relatório 4. 
Como a consulta procura especificamente pelos resultados de uma escuderia onde a posição de chegada foi 1, este índice reduz 
o custo de I/O, evitando uma varredura sequencial completa na tabela de resultados.
*/
CREATE INDEX idx_results_constructor_position ON results(constructor_id, position);

/* 
EXPLICAÇÃO JOIN, COUNT, GROUP BY, WHERE: Utilizou-se INNER JOIN para relacionar RESULTS, DRIVERS e CONSTRUCTORS. 
A função de agregação COUNT combinada com GROUP BY foi necessária para contabilizar as vitórias (position = '1') por piloto, 
enquanto o filtro WHERE restringe os dados apenas à escuderia autenticada, garantindo a segurança e o escopo exigidos no enunciado.
*/
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

-- Comando usado para testes no PGadmin4: SELECT * FROM get_relatorio4_escuderia('mclaren');

-- FIM SQL RELATÓRIO 4


-- SQL RELATÓRIO 5 (ESCUDERIAS)

/* 
EXPLICAÇÃO: A função centraliza a regra de negócio do Relatório 5. O uso de JOINs relaciona a tabela de resultados com a 
tabela de status descritivos, e o GROUP BY permite a contagem agregada de cada tipo de desfecho 
(ex: acidentes, finalizadas, problemas de motor), mantendo o isolamento dos dados através do filtro pela referência da escuderia.
*/
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

-- Comando usado para teste: SELECT * FROM get_relatorio5_escuderia('mclaren');
-- FIM SQL RELATÓRIO 5