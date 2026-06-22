import sqlite3
from pathlib import Path

DB_PATH = Path("data/asteroides.db")

def conectar():
    """Retorna uma conexão com o banco, criando-o se não existir."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # permite acessar colunas por nome
    return conn

def criar_schema():
    """Lê o arquivo SQL e cria as tabelas."""
    schema = Path("sql/schema.sql").read_text()
    with conectar() as conn:
        conn.executescript(schema)
    print("Schema criado com sucesso.")

def inserir_asteroides(asteroides: list[dict]):
    """Insere lista de asteroides, ignorando duplicatas pelo ID."""
    sql = """
        INSERT OR IGNORE INTO asteroides
            (id, nome, data_aproximacao, diametro_min_km, diametro_max_km,
             velocidade_kmh, distancia_km, distancia_lunar, e_perigoso, coletado_em)
        VALUES
            (:id, :nome, :data_aproximacao, :diametro_min_km, :diametro_max_km,
             :velocidade_kmh, :distancia_km, :distancia_lunar, :e_perigoso, :coletado_em)
    """
    with conectar() as conn:
        conn.executemany(sql, asteroides)
        print(f"{conn.total_changes} novos asteroides inseridos.")

def buscar_todos() -> list[dict]:
    """Retorna todos os asteroides como lista de dicionários."""
    with conectar() as conn:
        rows = conn.execute("SELECT * FROM asteroides ORDER BY data_aproximacao DESC").fetchall()
        return [dict(row) for row in rows]