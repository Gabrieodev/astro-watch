CREATE TABLE IF NOT EXISTS asteroides (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    data_aproximacao DATE NOT NULL,
    diametro_min_km REAL,
    diametro_max_km REAL,
    velocidade_kmh REAL NOT NULL,
    distancia_km REAL NOT NULL,
    distancia_lunar REAL NOT NULL,
    e_perigoso INTEGER NOT NULL, -- 0: FALSO, 1:VERDADEIRO
    score_risco REAL,
    coletado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS coletas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_inicio TEXT NOT NULL,
    data_fim TEXT NOT NULL,
    total_neos INTEGER,
    executado_em TEXT NOT NULL
);