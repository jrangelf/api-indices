# coding: utf-8
from sqlalchemy import BigInteger, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata

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
    

class T200TabelaPnep(Base):
    __tablename__ = 't200_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T202TabelaPnep(Base):
    __tablename__ = 't202_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T204TabelaPnep(Base):
    __tablename__ = 't204_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T206TabelaPnep(Base):
    __tablename__ = 't206_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T208TabelaPnep(Base):
    __tablename__ = 't208_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)    


class T210TabelaPnep(Base):
    __tablename__ = 't210_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T212TabelaPnep(Base):
    __tablename__ = 't212_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T214TabelaPnep(Base):
    __tablename__ = 't214_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T216TabelaPnep(Base):
    __tablename__ = 't216_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T218TabelaPnep(Base):
    __tablename__ = 't218_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T220TabelaPnep(Base):
    __tablename__ = 't220_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T222TabelaPnep(Base):
    __tablename__ = 't222_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T224TabelaPnep(Base):
    __tablename__ = 't224_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T226TabelaPnep(Base):
    __tablename__ = 't226_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T228TabelaPnep(Base):
    __tablename__ = 't228_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T230TabelaPnep(Base):
    __tablename__ = 't230_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T232TabelaPnep(Base):
    __tablename__ = 't232_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)


class T234TabelaPnep(Base):
    __tablename__ = 't234_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)

        
class T236TabelaPnep(Base):
    __tablename__ = 't236_tabela_pnep'

    id = Column(BigInteger, primary_key=True)
    data = Column(DateTime(True))
    indexador = Column(String(20))
    variacao_mensal = Column(Numeric)
    numero_indice = Column(Numeric)
    fator_vigente = Column(Numeric)
    indice_correcao = Column(Numeric)
    

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

