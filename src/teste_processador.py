from processador import calcular_scores, top_perigosos

df = calcular_scores()
print(df[["nome", "score_risco", "distancia_km", "velocidade_kmh"]].sort_values("score_risco", ascending=False).head())

print("\nTop 5 via heap:")
for ast in top_perigosos(5):
    print(f"{ast['nome']}: {ast['score_risco']}")