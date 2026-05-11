"""
database.py
===========
Módulo de infraestrutura de banco de dados da API de Índices PNRJ.

Responsabilidade:
    Configura e expõe o engine SQLAlchemy e a fábrica de sessões (SessionLocal)
    utilizados por toda a aplicação para acesso ao PostgreSQL.

Padrão utilizado:
    - Engine único criado na inicialização do módulo (singleton implícito).
    - SessionLocal instanciado com autocommit=False e autoflush=False, seguindo
      a convenção recomendada pelo FastAPI para gerenciamento de sessões por
      requisição (dependency injection via Depends).

Consumido por:
    - routers/tabelas.py  (injeção de sessão via get_db)
    - main.py             (criação das tabelas via Base.metadata.create_all)

Dependências:
    - sqlalchemy
    - constantes.py  (SQLALCHEMY_DATABASE_URL)
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from constantes import *

# postgresql://postgres_user:password@address/database_name
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:admin@pgsql/indexadores"

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
# Cria a conexão com o PostgreSQL usando a URL definida em constantes.py.
# Formato esperado: postgresql://usuario:senha@host:porta/banco
# Exemplo local:    postgresql://postgres:admin@pgsqlapi:5432/indices
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# ---------------------------------------------------------------------------
# Fábrica de sessões
# ---------------------------------------------------------------------------
# autocommit=False — commits devem ser feitos explicitamente.
# autoflush=False  — evita flushes automáticos antes de cada query,
#                    dando controle total ao código da aplicação.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------------------------------------------------------------------------
# Nota
# ---------------------------------------------------------------------------
# Base = declarative_base() está definido em models.py para que os modelos
# possam ser registrados independentemente deste módulo, evitando importações
# circulares. main.py importa Base de models.py e chama
# Base.metadata.create_all(bind=engine) para criar as tabelas na inicialização.

