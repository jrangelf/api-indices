"""
tools.py
========
Módulo de utilitários auxiliares da API de Índices PNRJ.

Responsabilidade:
    Fornece funções utilitárias de uso geral que não se encaixam nas
    camadas de banco de dados, modelos ou rotas, mas que são compartilhadas
    por múltiplos módulos da aplicação.

Funções disponíveis:
    - ajusta_nome_tabela(tabela_id)
        Converte um código numérico de tabela em nome de classe Python/ORM.

    - converter_var_per_mensal_para_porcentagem(tabela)
        Placeholder para conversão de variação mensal em percentual
        (implementação pendente).

Consumido por:
    - routers/tabelas.py
"""


def ajusta_nome_tabela(tabela_id: int) -> str:
    """
    Converte um código numérico de tabela no nome padronizado de classe ORM.

    O nome gerado segue o padrão utilizado pelos modelos em models.py:
        - Código com 1 dígito  → prefixo 'T0' + código  (ex: 1  → 'T01tabeladcp')
        - Código com 2+ dígitos → prefixo 'T'  + código  (ex: 200 → 'T200tabeladcp')

    Args:
        tabela_id (int): Código numérico identificador da tabela.

    Returns:
        str: Nome da classe ORM correspondente (ex: 'T200tabeladcp').

    Exemplo:
        >>> ajusta_nome_tabela(200)
        'T200tabeladcp'
        >>> ajusta_nome_tabela(5)
        'T05tabeladcp'

    Nota:
        Esta função é utilizada para construção dinâmica de queries via
        eval(tabela), permitindo consultar qualquer tabela pelo seu código
        sem hardcode. O uso de eval() requer validação prévia do código
        de entrada para evitar injeção de código.
    """
    code = str(tabela_id)
    # Adiciona zero à esquerda para códigos de 1 dígito (ex: '1' → 'T01...')
    pref = 'T0' + code if len(code) < 2 else 'T' + code
    return pref + 'tabeladcp'


def converter_var_per_mensal_para_porcentagem(tabela):
    """
    Converte a variação percentual mensal de uma tabela para formato de exibição.

    Args:
        tabela: Objeto de tabela ORM contendo o campo de variação mensal.

    Returns:
        None  (implementação pendente)

    Nota:
        Função atualmente sem implementação (placeholder).
        Prevista para converter o campo variacao_mensal (ex: 0.0075)
        em formato percentual legível (ex: 0.75%).
    """
    pass


