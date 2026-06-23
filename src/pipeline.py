from datetime import datetime, timedelta
from coletor import buscar_asteroides
from banco import criar_schema, inserir_asteroides
from processador import calcular_scores, top_perigosos
import schedule
import time

def executar_pipeline():
    print(f"\n[{datetime.now()}] Iniciando pipeline...")

    # Janela de 7 dias
    hoje = datetime.now().strftime("%Y-%m-%d")
    inicio = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    # Etapa 1: coleta
    asteroides = buscar_asteroides(inicio, hoje)
    print(f"Coletados: {len(asteroides)} asteroides")

    # Etapa 2: armazenamento
    inserir_asteroides(asteroides)

    # Etapa 3: scoring
    calcular_scores()

    # Resumo dos top perigosos
    top = top_perigosos(5)
    print("\nTop 5 mais perigosos esta semana:")
    for i, ast in enumerate(top, 1):
        print(f"  {i}. {ast['nome']} — score: {ast['score_risco']:.1f}")

    print(f"\n[{datetime.now()}] Pipeline concluído.")

if __name__ == "__main__":
    criar_schema()
    executar_pipeline()  # executa agora

    # Agenda para rodar toda semana às 08h de segunda-feira
    schedule.every().monday.at("08:00").do(executar_pipeline)

    print("\nScheduler ativo. Próxima execução: segunda-feira às 08h.")
    while True:
        schedule.run_pending()
        time.sleep(60)