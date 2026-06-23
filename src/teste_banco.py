from banco import criar_schema, inserir_asteroides, buscar_todos
from coletor import buscar_asteroides
from datetime import datetime, timedelta

criar_schema()

hoje = datetime.now().strftime("%Y-%m-%d")
semana_passada = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
dados = buscar_asteroides(semana_passada, hoje)
inserir_asteroides(dados)

resultado = buscar_todos()
print(f"Total no banco: {len(resultado)}")
print(resultado[0])