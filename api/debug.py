"""
debug.py
========
Módulo de configuração de logging da API de Índices PNRJ.

Responsabilidade:
    Configura o sistema de logging padrão do Python (basicConfig) para que
    todos os módulos da aplicação possam registrar mensagens em arquivo de log
    com nível, timestamp e mensagem formatados de forma consistente.

Configuração:
    - Nível mínimo : INFO  (registra INFO, WARNING, ERROR e CRITICAL)
    - Arquivo      : api.log  (criado no diretório de execução da aplicação)
    - Modo de escrita: 'a' — append; não sobrescreve logs anteriores
    - Formato      : NIVEL:TIMESTAMP:MENSAGEM

Uso nos demais módulos:
    Basta importar as funções de logging diretamente:

        from debug import info, warning, error

    E então chamar:

        info("Conexão estabelecida com sucesso")
        warning("Tabela sem registros: %s", nome_tabela)
        error("Falha ao consultar API: %s", str(exc))

Dependências:
    - logging (stdlib)

Consumido por:
    - routers/tabelas.py
    - (qualquer módulo que necessite registrar eventos)
"""


from logging import CRITICAL, ERROR, WARNING, INFO, DEBUG
from logging import critical, error, warning, info, debug
from logging import basicConfig


# ---------------------------------------------------------------------------
# Configuração global de logging
# ---------------------------------------------------------------------------
basicConfig(
    level=INFO,           # Registra INFO, WARNING, ERROR e CRITICAL
    filename='api.log',   # Arquivo de saída (relativo ao CWD da aplicação)
    filemode='a',         # Append — não apaga logs de execuções anteriores
    format='%(levelname)s:%(asctime)s:%(message)s'  # Ex: INFO:2024-01-15 10:30:00,123:Mensagem
)
