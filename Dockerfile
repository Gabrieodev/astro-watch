FROM python:3.12-slim

WORKDIR /app

COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

COPY . .

# Cria o diretório de dados persistido
RUN mkdir -p data

CMD ["python", "src/pipeline.py"]