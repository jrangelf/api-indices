"""
models.py
=========
Módulo de modelos ORM (SQLAlchemy) da API de Índices PNRJ.

Responsabilidade:
    Define o mapeamento objeto-relacional (ORM) entre as classes Python e as
    tabelas do banco de dados PostgreSQL. Cada classe representa uma tabela
    do banco e herda de Base (declarative_base).

Organização das tabelas por grupo e faixa de código:
    ┌──────────────────────────────────────────────────────┐
    │ Grupo               │ Código    │ Classes            │
    ├──────────────────────────────────────────────────────┤
    │ Indexadores BCB     │ < 200     │ Selic, SelicCopom, │
    │                     │           │ Tr, Inpc, Ipca,    │
    │                     │           │ Ipca15, Igpm       │
    ├──────────────────────────────────────────────────────┤
    │ Índices PNRJ        │ 200–299   │ T200 … T236        │
    ├──────────────────────────────────────────────────────┤
    │ Juros               │ 300–399   │ T300 … T334        │
    ├──────────────────────────────────────────────────────┤
    │ Índices adicionais  │ 400–499   │ T400 … T408        │
    │ (crédito)           │           │                    │
    ├──────────────────────────────────────────────────────┤
    │ Controle/metadados  │ —         │ LogAtualizacao,    │
    │                     │           │ DescricaoTabelas,  │
    │                     │           │ RegraAtualizacao,  │
    │                     │           │ Indexadores        │
    └──────────────────────────────────────────────────────┘

Base de dados:
    PostgreSQL — banco 'indices' conforme configurado em pgsqlapi.env.

Consumido por:
    - main.py          (Base.metadata.create_all)
    - routers/tabelas.py (consultas ORM via Session)

Dependências:
    - sqlalchemy
"""

# coding: utf-8
from sqlalchemy import BigInteger, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.ext.declarative import declarative_base

# ---------------------------------------------------------------------------
# Base declarativa — ponto de registro de todos os modelos ORM
# ---------------------------------------------------------------------------
Base = declarative_base()
metadata = Base.metadata

# ===========================================================================
# INDEXADORES BCB (código < 200)
# Séries temporais brutas coletadas diretamente da API pública do BCB (SGS).
# Cada registro contém: id, data (mês de referência), valor (taxa/índice).
# Alimentados pelo sistema PNRJ via pnrj_indexadores.py.
# ===========================================================================

class Selic(Base):
    __tablename__ = 'selic'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    valor = Column(Numeric)
    

class SelicCopom(Base):
    __tablename__ = 'seliccopom'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    valor = Column(Numeric)
    

class Tr(Base):
    __tablename__ = 'tr'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    valor = Column(Numeric)
    

class Inpc(Base):
    __tablename__ = 'inpc'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    valor = Column(Numeric)


class Ipca(Base):
    __tablename__ = 'ipca'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    valor = Column(Numeric)


class Ipca15(Base):
    __tablename__ = 'ipca15'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    valor = Column(Numeric)

class Igpm(Base):
    __tablename__ = 'igpm'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    valor = Column(Numeric)    

# ===========================================================================
# TABELAS DE CONTROLE E METADADOS
# Tabelas auxiliares para gerenciamento e autodescoberta das demais tabelas.
# ===========================================================================

class LogAtualizacao(Base):    
    __tablename__ = 'logatualizacao'

    id = Column(BigInteger, primary_key=True)
    codigo_tabela = Column(Integer)
    indexador = Column(Integer)
    data_atualizacao = Column(DateTime(True))
    processar = Column(Integer)
    

class DescricaoTabelas(Base):
    __tablename__ = 'descricao_tabelas'

    id = Column(BigInteger, primary_key=True)
    codigo = Column(Integer)
    nome = Column(String(20))
    descricao = Column(String(200))
    regra_de_calculo = Column(Integer)
    observacao = Column(Text)
    indexador = Column(Integer)


class RegraAtualizacao(Base):
    __tablename__ = 'regra_atualizacao'

    id = Column(BigInteger, primary_key=True)
    tipo = Column(Integer)
    nome = Column(String(20))
    descricao = Column(Text)
    

class Indexadores(Base):
    __tablename__ = 'indexadores'

    id = Column(BigInteger, primary_key=True)
    codigo = Column(Integer)
    nome = Column(String(20))
    descricao = Column(String(100))
    
# ===========================================================================
# TABELAS DE ÍNDICES PNRJ (código 200–299)
# Tabelas de correção monetária calculadas com base nos indexadores BCB.
# Cada tabela representa uma combinação de indexador + data-base de cálculo.
#
# Estrutura comum a todas as tabelas TxxxTabelaPnrj:
#   data             — mês de referência
#   indexador        — nome do indexador base (ex: 'IPCA', 'TR')
#   variacao_mensal  — variação percentual do indexador no mês (valor/100)
#   numero_indice    — 1 + variacao_mensal
#   fator_vigente    — fator_anterior × numero_indice (acumulado desde data-base)
#   indice_correcao  — índice de correção relativo ao último mês da série
#                      (recalculado integralmente a cada atualização)
#
# Fórmulas:
#   variacao_mensal  = valor_bcb / 100
#   numero_indice    = 1 + variacao_mensal
#   fator_vigente    = fator_vigente_anterior × numero_indice
#   indice_correcao  = fator_vigente_último / fator_vigente (para cada linha)
# ===========================================================================

class T200TabelaPnrj(Base):
    __tablename__ = 't200_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T202TabelaPnrj(Base):
    __tablename__ = 't202_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T204TabelaPnrj(Base):
    __tablename__ = 't204_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T206TabelaPnrj(Base):
    __tablename__ = 't206_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T208TabelaPnrj(Base):
    __tablename__ = 't208_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)    


class T210TabelaPnrj(Base):
    __tablename__ = 't210_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T212TabelaPnrj(Base):
    __tablename__ = 't212_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T214TabelaPnrj(Base):
    __tablename__ = 't214_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T216TabelaPnrj(Base):
    __tablename__ = 't216_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T218TabelaPnrj(Base):
    __tablename__ = 't218_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T220TabelaPnrj(Base):
    __tablename__ = 't220_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T222TabelaPnrj(Base):
    __tablename__ = 't222_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T224TabelaPnrj(Base):
    __tablename__ = 't224_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T226TabelaPnrj(Base):
    __tablename__ = 't226_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T228TabelaPnrj(Base):
    __tablename__ = 't228_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T230TabelaPnrj(Base):
    __tablename__ = 't230_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T232TabelaPnrj(Base):
    __tablename__ = 't232_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T234TabelaPnrj(Base):
    __tablename__ = 't234_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)

        
class T236TabelaPnrj(Base):
    __tablename__ = 't236_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)
    
# ===========================================================================
# TABELAS DE JUROS (código 300–399)
# Taxas de juros mensais e acumuladas calculadas pelo sistema PNRJ.
# As tabelas de juros derivados (T302–T334) são calculadas com base
# na taxa da poupança (T300) e/ou na SELIC acumulada (T312).
# ===========================================================================

class T300Juros(Base):
    __tablename__ = 't300_juros_poupanca'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    meta_selic_copom = Column(Numeric)
    taxa_mensal = Column(Numeric)


class T302Juros(Base):
    __tablename__ = 't302_juros'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    juros_mensal = Column(Numeric)
    juros_acumulados = Column(Numeric)


class T304Juros(Base):
    __tablename__ = 't304_juros'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    juros_mensal = Column(Numeric)
    juros_acumulados = Column(Numeric)


class T306Juros(Base):
    __tablename__ = 't306_juros'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    juros_mensal = Column(Numeric)
    juros_acumulados = Column(Numeric)


class T308Juros(Base):
    __tablename__ = 't308_juros'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    juros_mensal = Column(Numeric)
    juros_acumulados = Column(Numeric)


class T310Juros(Base):
    __tablename__ = 't310_juros'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    juros_mensal = Column(Numeric)
    juros_acumulados = Column(Numeric)

class T310JurosPnn(Base):
    __tablename__ = 't310_juros_pnn'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    juros_mensal = Column(Numeric)
    juros_acumulados = Column(Numeric)

class T312Selic(Base):
    __tablename__ = 't312_selic'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    selic = Column(Numeric)
    selic_acumulada = Column(Numeric)
    selic_acumulada_mensal = Column(Numeric)

# -------------------------------
# Tabelas de juros para crédito 
# -------------------------------

class T322Juros(Base):
    __tablename__ = 't322_juros'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    juros_mensal = Column(Numeric)
    juros_acumulados = Column(Numeric)

class T324Juros(Base):
    __tablename__ = 't324_juros'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    juros_mensal = Column(Numeric)
    juros_acumulados = Column(Numeric)

class T326Juros(Base):
    __tablename__ = 't326_juros'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    juros_mensal = Column(Numeric)
    juros_acumulados = Column(Numeric)

class T328Juros(Base):
    __tablename__ = 't328_juros'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    juros_mensal = Column(Numeric)
    juros_acumulados = Column(Numeric)

class T330Juros(Base):
    __tablename__ = 't330_juros'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    juros_mensal = Column(Numeric)
    juros_acumulados = Column(Numeric)

class T332Selic(Base):
    __tablename__ = 't332_selic'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    selic = Column(Numeric)
    selic_acumulada = Column(Numeric)
    selic_acumulada_mensal = Column(Numeric)

class T334Selic(Base):
    __tablename__ = 't334_selic'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    selic = Column(Numeric)
    selic_acumulada = Column(Numeric)
    selic_acumulada_mensal = Column(Numeric)


# ===========================================================================
# TABELAS DE ÍNDICES — CRÉDITO (código 400–499)
# Mesma estrutura das tabelas 200–299, mas com data-base e indexadores
# específicos para uso em contratos de crédito.
# ===========================================================================

class T400TabelaPnrj(Base):
    __tablename__ = 't400_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T402TabelaPnrj(Base):
    __tablename__ = 't402_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T404TabelaPnrj(Base):
    __tablename__ = 't404_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T406TabelaPnrj(Base):
    __tablename__ = 't406_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)

class T408TabelaPnrj(Base):
    __tablename__ = 't408_tabela_pnrj'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)