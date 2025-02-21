# coding: utf-8
from sqlalchemy import BigInteger, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class TabelaIndexador(Base):
    """ Classe base para tabelas de indexadores econômicos. """
    __abstract__ = True
    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    valor = Column(Numeric)

# Índexadores Econômicos do Banco Central 
class Selic(TabelaIndexador): __tablename__ = 'selic'
class SelicCopom(TabelaIndexador): __tablename__ = 'seliccopom'
class Tr(TabelaIndexador): __tablename__ = 'tr'
class Inpc(TabelaIndexador): __tablename__ = 'inpc'
class Ipca(TabelaIndexador): __tablename__ = 'ipca'
class Ipca15(TabelaIndexador): __tablename__ = 'ipca15'
class Igpm(TabelaIndexador): __tablename__ = 'igpm'


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
    

# Tabelas PNEP 
class TabelaPnep(Base):
    __abstract__ = True
    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T200TabelaPnep(TabelaPnep): __tablename__ = 't200_tabela_pnep'
class T202TabelaPnep(TabelaPnep): __tablename__ = 't202_tabela_pnep'
class T204TabelaPnep(TabelaPnep): __tablename__ = 't204_tabela_pnep'
class T206TabelaPnep(TabelaPnep): __tablename__ = 't206_tabela_pnep'
class T208TabelaPnep(TabelaPnep): __tablename__ = 't208_tabela_pnep'
class T210TabelaPnep(TabelaPnep): __tablename__ = 't210_tabela_pnep'
class T212TabelaPnep(TabelaPnep): __tablename__ = 't212_tabela_pnep'
class T214TabelaPnep(TabelaPnep): __tablename__ = 't214_tabela_pnep'
class T216TabelaPnep(TabelaPnep): __tablename__ = 't216_tabela_pnep'
class T218TabelaPnep(TabelaPnep): __tablename__ = 't218_tabela_pnep'
class T220TabelaPnep(TabelaPnep): __tablename__ = 't220_tabela_pnep'
class T222TabelaPnep(TabelaPnep): __tablename__ = 't222_tabela_pnep'
class T224TabelaPnep(TabelaPnep): __tablename__ = 't224_tabela_pnep'
class T226TabelaPnep(TabelaPnep): __tablename__ = 't226_tabela_pnep'
class T228TabelaPnep(TabelaPnep): __tablename__ = 't228_tabela_pnep'
class T230TabelaPnep(TabelaPnep): __tablename__ = 't230_tabela_pnep'
class T232TabelaPnep(TabelaPnep): __tablename__ = 't232_tabela_pnep'
class T234TabelaPnep(TabelaPnep): __tablename__ = 't234_tabela_pnep'
class T236TabelaPnep(TabelaPnep): __tablename__ = 't236_tabela_pnep'
#class T238TabelaPnep(TabelaPnep): __tablename__ = 't238_tabela_pnep'
#class T240TabelaPnep(TabelaPnep): __tablename__ = 't240_tabela_pnep'
    

class TabelaJuros(Base):
    __abstract__ = True

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    juros_mensal = Column(Numeric)
    juros_acumulados = Column(Numeric)

class T300Juros(Base):
    __tablename__ = 't300_juros_poupanca'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    meta_selic_copom = Column(Numeric)
    taxa_mensal = Column(Numeric)


class T302Juros(TabelaJuros): __tablename__ = 't302_juros'
class T304Juros(TabelaJuros): __tablename__ = 't304_juros'
class T306Juros(TabelaJuros): __tablename__ = 't306_juros'
class T308Juros(TabelaJuros): __tablename__ = 't308_juros'
class T310Juros(TabelaJuros): __tablename__ = 't310_juros'


class T312Selic(Base):
    __tablename__ = 't312_selic'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    selic = Column(Numeric)
    selic_acumulada = Column(Numeric)
    selic_acumulada_mensal = Column(Numeric)


class T400Tabela(Base):
    __tablename__ = 'serie_historica_moedas'

    id = Column(BigInteger, primary_key=True)
    vigencia = Column(String(20))
    moeda = Column(String(20))
    alteracao = Column(String(150))
    legislacao = Column(Text)


