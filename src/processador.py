import pandas as pd
import heapq
from banco import conectar

def calcular_scores():
    """
    Calcula o score de risco para todos os asteroides.
    Usa normalização Min-Max para comparar grandezas diferentes.
    """
    with conectar() as conn:
        df = pd.read_sql("SELECT * FROM asteroides", conn)

    if df.empty:
        print("Banco vazio. Execute a coleta primeira.")
        return
    
     # Diâmetro médio entre min e max estimado pela NASA
    df["diametro_medio"] = (df["diametro_min_km"] + df["diametro_max_km"]) / 2

    # Risco bruto — antes de normalizar
    df["risco_bruto"] = (1 / df["distancia_km"]) * df["velocidade_kmh"] * df["diametro_medio"]

    # Normalização Min-Max: transforma cada coluna para [0, 1]
    def normalizar(serie):
        min_val = serie.min()
        max_val = serie.max()
        if max_val == min_val:
            return pd.Series([0,0] * len(serie))
        return (serie - min_val) / (max_val - min_val)
    
    df["score_distancia"] = 1 - normalizar(df["distancia_km"])  # menor distância = maior risco
    df["score_velocidade"] = normalizar(df["velocidade_kmh"])
    df["score_tamanho"]    = normalizar(df["diametro_medio"])

    # Score final ponderado (pesos somam 1.0)
    df["score_risco"] = (
        df["score_distancia"] * 0.50 +
        df["score_velocidade"] * 0.30 +
        df["score_tamanho"]   * 0.20
    ) * 100  # escala 0–100

    # Atualiza o banco com os scores calculados
    with conectar() as conn:
        for _, row in df.iterrows():
            conn.execute(
                "UPDATE asteroides SET score_risco = ? WHERE id = ?",
                (round(row["score_risco"], 2), row["id"])
            )
    print(f"Scores calculados para {len(df)} asteroides.")
    return df

def top_perigosos(n: int = 10) -> list[tuple]:
    """
    Retorna os N asteroides mais perigosos usando um max-heap.
    Heap é mais eficiente que ordenar tudo quando N << total.
    """
    with conectar() as conn:
        todos = conn.execute(
            "SELECT nome, score_risco, distancia_km, velocidade_kmh FROM asteroides WHERE score_risco IS NOT NULL"
        ).fetchall()

    # heapq é um min-heap; negamos o score para simular max-heap
    heap = []
    for row in todos:
        heapq.heappush(heap, (-row["score_risco"], dict(row)))

    return [heapq.heappop(heap)[1] for _ in range(min(n, len(heap)))]