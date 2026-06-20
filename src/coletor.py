import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("NASA_API_KEY")

def buscar_asteroides(data_inicio: str, data_fim: str) -> list[dict]:
    """
    Busca asteroides próximos à Terra em um intervalo de datas.
    Retorna lista de dicionários, um por asteroide.
    """
    url = "https://api.nasa.gov/neo/rest/v1/feed"
    params = {
        "start_date": data_inicio,
        "end_date": data_fim,
        "api_key": API_KEY
    }

    resposta = requests.get(url, params=params)
    resposta.raise_for_status()  # lança erro se status != 200
    dados = resposta.json()

    asteroides = []

    # O JSON tem uma chave "near_earth_objects" com datas como sub-chaves
    for data, lista in dados["near_earth_objects"].items():
        for neo in lista:

            # Utilizando a aproximação mais próxima
            aproximacao = neo["close_approach_data"][0]

            asteroide = {
                "id": neo["id"],
                "nome": neo["name"],
                "data_aproximacao": aproximacao["close_approach_date"],
                "diametro_min_km": float(neo["estimated_diameter"]["kilometers"]["estimated_diameter_min"]),
                "diametro_max_km": float(neo["estimated_diame ter"]["kilometers"]["estimated_diameter_max"]),
                "velocidade_kmh": float(aproximacao["relative_velocity"]["kilometers_per_hour"]),
                "distancia_km": float(aproximacao["miss_distance"]["kilometers"]),
                "distancia_lunar": float(aproximacao["miss_distance"]["lunar"]),
                "e_perigoso": neo["is_potentially_hazardous_asteroid"],
                "coletado_em": datetime.now().isoformat()
            }
            asteroides.append(asteroide)

    return asteroides


if __name__ == "__main__":
    hoje = datetime.now().strftime("%Y-%m-%d")
    semana_passada = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    resultado = buscar_asteroides(semana_passada, hoje)
    print(f"Asteroides coletados: {len(resultado)}")
    print(json.dumps(resultado[0], indent=2, ensure_ascii=False))