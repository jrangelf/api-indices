"""
constantes.py
=============
Módulo de configuração global da API de Índices PNRJ.

Responsabilidade:
    Carrega variáveis de ambiente via python-decouple e as disponibiliza
    como constantes globais para todos os módulos da aplicação.

Variáveis de ambiente esperadas (.env):
    SQLALCHEMY_DB_URL  — URL de conexão com o PostgreSQL no formato:
                         postgresql://usuario:senha@host:porta/banco

Consumido por:
    - database.py

Dependências:
    - python-decouple
"""

from decouple import config, Csv

# ---------------------------------------------------------------------------
# Conexão com o banco de dados
# ---------------------------------------------------------------------------

# URL de conexão SQLAlchemy com o PostgreSQL.
# Formato esperado: postgresql://usuario:senha@host:porta/nome_banco
# Exemplo:          postgresql://postgres:admin@pgsqlapi:5432/indices
SQLALCHEMY_DATABASE_URL = config('SQLALCHEMY_DB_URL')


# ---------------------------------------------------------------------------
# Mensagens padrão
# ---------------------------------------------------------------------------

# Mensagem retornada pela API quando uma consulta não encontra registros.
# Utilizada em HTTPException(status_code=404, detail=NOREGS).
NOREGS = 'Não há registro'