import ollama
from banco import conectar

SYSTEM_PROMPT = """
Você é AstroBot, um assistente especialista em astronomia e asteroides.
Você recebe dados reais da NASA sobre um asteroide e deve:
1. Contextualizar o risco em linguagem acessível (não use jargão técnico puro)
2. Contar uma curiosidade científica interessante sobre o objeto ou sua classe
3. Fazer uma analogia criativa para ajudar o usuário a compreender o tamanho ou velocidade
4. Ser preciso mas engajante — você fala com curiosos sobre ciência, não com especialistas

Responda sempre em português brasileiro. Máximo 3 parágrafos.
"""

def gerar_ficha_asteroide(asteroid_id: str) -> str:
    """
    Gera uma ficha narrativa sobre um asteroide usando o Ollama.
    """
    with conectar() as conn:
        row = conn.execute(
            "SELECT * FROM asteroides WHERE id = ?", (asteroid_id,)
        ).fetchone()

    if not row:
        return "Asteroide não encontrado no banco."

    # Construindo o prompt com dados reais
    prompt_usuario = f"""
    Analise este asteroide detectado pela NASA e me forneça informações:

    Nome: {row['nome']}
    Data de aproximação: {row['data_aproximacao']}
    Diâmetro estimado: {row['diametro_min_km']:.2f} a {row['diametro_max_km']:.2f} km
    Velocidade relativa: {row['velocidade_kmh']:,.0f} km/h
    Distância mínima da Terra: {row['distancia_km']:,.0f} km ({row['distancia_lunar']:.1f} distâncias lunares)
    Classificado como potencialmente perigoso: {'Sim' if row['e_perigoso'] else 'Não'}
    Score de risco calculado: {row['score_risco']:.1f}/100
    """

    resposta = ollama.chat(
        model="llama3",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt_usuario}
        ]
    )

    return resposta["message"]["content"]

def chat_interativo():
    """
    Loop de conversa onde o usuário pode perguntar sobre qualquer asteroide
    ou fazer perguntas gerais sobre astronomia.
    """
    print("\n=== AstroBot — Assistente de Asteroides ===")
    print("Digite 'sair' para encerrar. Digite um nome de asteroide para detalhes.\n")

    historico = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        entrada = input("Você: ").strip()
        if entrada.lower() == "sair":
            break

        historico.append({"role": "user", "content": entrada})
        resposta = ollama.chat(model="llama3", messages=historico)
        conteudo = resposta["message"]["content"]

        historico.append({"role": "assistant", "content": conteudo})
        print(f"\nAstroBot: {conteudo}\n")