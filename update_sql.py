import psycopg2

sql = """
CREATE INDEX IF NOT EXISTS idx_results_driver_points ON results(driver_id, points);
CREATE INDEX IF NOT EXISTS idx_races_season_id ON races(season_id);

DROP FUNCTION IF EXISTS relatorio_6_pontos_piloto(INTEGER);

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
"""

try:
    conn = psycopg2.connect(host='pgdb.icmc.usp.br', dbname='scc541_g12_db', user='scc541_g12', password='grupo12_Gabriel_2026', port=5432)
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    print("SQL Update Success")
except Exception as e:
    print("Error:", e)
finally:
    if 'conn' in locals():
        conn.close()
