"""
main.py
=======
Entry point da API de Índices PNRJ (api-indice).

Responsabilidade:
    - Instancia a aplicação FastAPI.
    - Garante a criação automática das tabelas no PostgreSQL na inicialização
      (Base.metadata.create_all), caso ainda não existam.
    - Registra o router principal (tabelas.router), que define todos os
      endpoints da API.

Execução:
    Gerenciada pelo Uvicorn conforme configurado no Dockerfile:

        uvicorn main:app --host 0.0.0.0 --port 8004 --reload

    Em desenvolvimento local:

        uvicorn main:app --reload --port 8004

Endpoints registrados:
    Todos os endpoints são definidos em routers/tabelas.py e montados
    sem prefixo de rota, ficando disponíveis diretamente na raiz da API.
    Exemplos:
        GET /ipca/{mes}/{ano}
        GET /selic/periodo
        GET /t200_tabela_pnrj
        GET /t312_selic/{mes}/{ano}

Dependências:
    - fastapi
    - database.py   (engine para criação das tabelas)
    - models.py     (Base com todos os modelos ORM registrados)
    - routers/tabelas.py  (router com os endpoints)
"""

# ---------------------------------------------------------------------------
# Instância da aplicação FastAPI
# ---------------------------------------------------------------------------
from fastapi import FastAPI
from database import engine 
from routers import tabelas
from models import *

app = FastAPI(
    title="API de Índices PNRJ",
    description=(
        "API REST para consulta de indexadores econômicos (BCB), "
        "índices de correção monetária PNRJ e tabelas de juros. "
        "Os dados são atualizados automaticamente pelo sistema PNEP."
    ),
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Criação automática das tabelas no PostgreSQL
# ---------------------------------------------------------------------------
# Cria todas as tabelas mapeadas em models.py caso ainda não existam.
# Em produção, prefira migrações explícitas (ex: Alembic) no lugar desta linha.
Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Registro de routers
# ---------------------------------------------------------------------------
# Monta o router de tabelas sem prefixo, expondo todos os endpoints na raiz.
app.include_router(tabelas.router)




