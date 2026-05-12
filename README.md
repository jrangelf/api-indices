# api-indice — API REST de Índices e Correção Monetária PNRJ

> **API FastAPI que expõe indexadores econômicos do Banco Central e índices de correção monetária calculados pelo sistema PNRJ — dados prontos para consumo por qualquer aplicação financeira.**

---

## Sobre o Projeto

A **api-indice** é a camada de acesso público do ecossistema PNRJ. Ela conecta-se ao banco de dados PostgreSQL que é alimentado e mantido pelo **[sistema PNRJ](../PNRJ/README.md)** — responsável pela coleta automática dos indexadores no Banco Central do Brasil e pelo cálculo dos índices de correção monetária e juros.

Enquanto o sistema PNRJ **escreve** os dados periodicamente, a **api-indice** os **lê e os expõe** via endpoints REST, permitindo que outras aplicações consumam taxas econômicas atualizadas (IPCA, SELIC, TR, IGPM, INPC, IPCA-15) e índices de correção PNRJ sem precisar acessar diretamente o banco ou a API do Banco Central.

```
┌──────────────────────────────────────────────────────────┐
│                    Ecossistema PNRJ                      │
│                                                          │
│  [API BCB/SGS] ──▶ [Sistema PNRJ] ──▶ [PostgreSQL]       │
│                                              │           │
│                                              ▼           │
│                                      [api-indice]        │
│                                          :8004           │
│                                              │           │
│                          ┌───────────────────┤           │
│                          ▼                   ▼           │
│                   [App Financeira]   [Sistema PNRJ]      │
│                   (consumidor)       (consultas internas)│
└──────────────────────────────────────────────────────────┘
```

---

## Funcionalidades

- **Indexadores BCB** — Consulta de IPCA, IPCA-15, INPC, TR, SELIC, SELIC COPOM e IGPM por mês/ano ou período
- **Índices de Correção PNRJ** — Acesso às tabelas de fator vigente e índice de correção (T200 a T408) com variação mensal, número índice e correção acumulada
- **Juros** — Tabelas de juros da poupança, SELIC acumulada e juros derivados para uso em contratos de crédito (T300 a T334)
- **Metadados** — Endpoints de descoberta: catálogo de tabelas, regras de cálculo e log de atualização
- **3 modos de consulta por tabela**: registro único (`/{tabela}/{mes}/{ano}`), série completa (`/{tabela}`) e intervalo (`/{tabela}/periodo`)
- **Validação de parâmetros** — Verificação automática de intervalos de mês (1–12), ano e coerência de períodos (início ≤ fim)
- **Containerizado** — Deploy completo com Docker Compose (API + PostgreSQL em rede dedicada)
- **Logging** — Registro de eventos em `api.log` com nível, timestamp e mensagem

---

## Arquitetura

### Estrutura de Arquivos

```
api-indice/
├── main.py              # Entry point FastAPI — inicialização e registro do router
├── models.py            # Modelos ORM SQLAlchemy (40+ tabelas mapeadas)
├── database.py          # Engine e SessionLocal (fábrica de sessões)
├── constantes.py        # Variáveis de ambiente e constantes globais
├── debug.py             # Configuração de logging
├── tools.py             # Utilitários auxiliares
├── routers/
│   └── tabelas.py       # Todos os endpoints GET da API
├── requirements.txt     # Dependências Python
├── dockerfile.api       # Imagem Docker da API (Ubuntu + Python 3)
└── .env                 # Variáveis de ambiente (não versionar)
```

### Fluxo de uma Requisição

```
Cliente HTTP
    │
    ▼ GET /ipca/3/2024
[FastAPI — main.py]
    │  app.include_router(tabelas.router)
    ▼
[routers/tabelas.py]
    │  get_db() → SessionLocal()
    │  db.query(Ipca).filter(year==2024, month==3).first()
    ▼
[database.py]
    │  engine → postgresql://...
    ▼
[PostgreSQL — banco 'indices']
    │  SELECT * FROM ipca WHERE EXTRACT(year FROM data)=2024 ...
    ▼
[models.py — class Ipca]
    │  formatar_data() → data.strftime('%d/%m/%Y')
    ▼
JSON Response: {"id": 1, "data": "01/03/2024", "valor": 0.83}
```

### Grupos de Tabelas

| Grupo | Faixa de código | Tabelas | Consulta via |
|-------|----------------|---------|--------------|
| Indexadores BCB | — | `ipca`, `inpc`, `tr`, `selic`, `seliccopom`, `igpm`, `ipca15` | `/ipca`, `/selic`, ... |
| Índices PNRJ | 200–299 | `t200` a `t236_tabela_PNRJ` | `/t200_tabela_PNRJ`, ... |
| Juros | 300–399 | `t300_juros_poupanca`, `t302`–`t312_selic` | `/t300_juros_poupanca`, ... |
| Juros crédito | 320–334 | `t322`–`t334` | `/t322_juros`, ... |
| Índices crédito | 400–499 | `t400`–`t408_tabela_PNRJ` | `/t400_tabela_PNRJ`, ... |
| Metadados | — | `descricao_tabelas`, `logatualizacao`, `indexadores` | `/descricao_tabelas`, ... |

---

## Endpoints

### Padrão de rotas (repetido para cada indexador/tabela)

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/{tabela}` | Série histórica completa |
| `GET` | `/{tabela}/{mes}/{ano}` | Registro do mês/ano específico |
| `GET` | `/{tabela}/periodo?mes_inicial=&ano_inicial=&mes_final=&ano_final=` | Intervalo de meses |

### Endpoints de metadados

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/bcb` | Resumo do último registro de todos os indexadores BCB |
| `GET` | `/descricao_tabelas` | Catálogo completo de tabelas |
| `GET` | `/nome_tabelas` | Lista simplificada: código, nome e descrição |
| `GET` | `/indexadores` | Catálogo de indexadores BCB disponíveis |
| `GET` | `/logatualizacao` | Log de atualização e agendamento das tabelas |

### Exemplos de requisição

```bash
# Último valor de todos os indexadores
curl http://localhost:8004/bcb

# IPCA de março de 2024
curl http://localhost:8004/ipca/3/2024

# SELIC de janeiro a dezembro de 2023
curl "http://localhost:8004/selic/periodo?mes_inicial=1&ano_inicial=2023&mes_final=12&ano_final=2023"

# Índice de correção PNRJ T200 — série completa
curl http://localhost:8004/t200_tabela_PNRJ

# Juros da poupança de abril de 2024
curl http://localhost:8004/t300_juros_poupanca/4/2024
```

### Respostas de erro

| Código | Situação |
|--------|----------|
| `400` | Período inválido: data inicial > data final |
| `404` | Nenhum registro encontrado para o filtro informado |

---

## Tecnologias

| Categoria | Tecnologia |
|-----------|-----------|
| Framework web | FastAPI + Uvicorn |
| ORM | SQLAlchemy |
| Banco de dados | PostgreSQL 15.3 |
| DB Driver | psycopg2-binary |
| Config / Env | python-decouple |
| Containerização | Docker + Docker Compose |
| Logging | logging (stdlib) |
| Linguagem | Python 3 (Ubuntu Focal) |

---

## Instalação e Execução

### Pré-requisitos

- Docker e Docker Compose instalados
- Rede Docker `indices` criada (compartilhada com o sistema PNRJ)

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/api-indice.git
cd api-indice
```

### 2. Configure as variáveis de ambiente

Crie o arquivo `env/pgsqlapi.env` para o banco:

```env
POSTGRES_PASSWORD=admin
POSTGRES_USER=postgres
POSTGRES_DB=indices
PGDATA=/var/lib/postgresql/data/pgdata
```

Crie o arquivo `api/.env` para a API:

```env
SQLALCHEMY_DB_URL=postgresql://postgres:admin@pgsqlapi:5432/indices
```

### 3. Crie a rede Docker compartilhada

```bash
docker network create indices
```

### 4. Suba os containers

```bash
docker compose up -d --build
```

### 5. Verifique a API

```bash
# Health check
curl http://localhost:8004/bcb

# Documentação interativa (Swagger)
open http://localhost:8004/docs

# Documentação alternativa (ReDoc)
open http://localhost:8004/redoc
```

### Execução em desenvolvimento local (sem Docker)

```bash
cd api
pip install -r requirements.txt

# Configure o .env com URL do PostgreSQL local
echo "SQLALCHEMY_DB_URL=postgresql://postgres:admin@localhost:5432/indices" > .env

uvicorn main:app --reload --port 8004
```

---

## Estrutura Docker

```yaml
# docker-compose.yml
services:
  pgsqlapi:          # PostgreSQL 15.3 — porta 5438:5432
    image: pgsqlapi:latest
    volumes:
      - ./pgsqlapi/db:/var/lib/postgresql/data
      - ./pgsqlapi/backup:/db/backup

  api-indice:        # FastAPI + Uvicorn — porta 8004:8004
    image: api-indice:latest
    volumes:
      - ./api:/api   # Hot-reload em desenvolvimento (--reload)

networks:
  indices:           # Rede compartilhada com o sistema PNRJ
    external: true
```

---

## Integração com o Sistema PNRJ

Esta API é consumida internamente pelo **sistema PNRJ** (`PNRJ_api_index.py`) para consulta de valores de indexadores já processados durante o cálculo dos índices de correção monetária e juros. Os dados que a API expõe são escritos pelo próprio sistema PNRJ — formando um ciclo fechado:

```
[BCB SGS] → [PNRJ_api_bcb.py] → [PostgreSQL] → [api-indice :8004]
                                                        ↑
                                          [PNRJ_api_index.py consulta aqui]
                                          para calcular índices e juros
```

---

## Pontos de Atenção

- **`Base.metadata.create_all`** em `main.py` cria as tabelas automaticamente na primeira inicialização. Em ambientes de produção com esquema estabelecido, considere substituir por migrações explícitas (Alembic).
- **Modo `--reload`** do Uvicorn está ativo no Dockerfile — adequado para desenvolvimento, mas desabilite em produção.
- **Formatação de datas**: todos os retornos formatam `data` para `DD/MM/YYYY`. Parsers do lado do cliente devem estar preparados para este formato.
- **Tabelas T406 e T408** retornam código de status `406` e `408` respectivamente em caso de 404 — comportamento legado que pode ser corrigido para o padrão `404`.

---

## Contribuição

1. Faça um **fork** do repositório
2. Crie uma branch: `git checkout -b feature/minha-feature`
3. Commit: `git commit -m 'feat: adiciona novo endpoint'`
4. Push: `git push origin feature/minha-feature`
5. Abra um **Pull Request**

---

## Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para detalhes.

---

<div align="center">
  <sub>Parte do ecossistema PNRJ · Dados econômicos do <a href="https://www.bcb.gov.br/">Banco Central do Brasil</a> · FastAPI + PostgreSQL</sub>
</div>
