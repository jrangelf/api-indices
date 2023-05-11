# coding: utf-8
from sqlalchemy import BigInteger, Column, DateTime, Integer, Numeric, String, text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class C01tabelainventario(Base):
    __tablename__ = 'c01tabelainventario'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t21listatabelasdcp_id_seq'::regclass)"))
    C01_CODIGO = Column(Integer)
    C01_NOME_TABELA = Column(String(50))
    C01_OBS_TABELA = Column(String(1000))
    C01_INDEXADOR = Column(String(30))


class C02tabelaindexadoresdcp(Base):
    __tablename__ = 'c02tabelaindexadoresdcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t03indexadoresdcp_id_seq'::regclass)"))
    C02_CODIGO = Column(String(20))
    C02_NOME_INDEXADOR = Column(String(50))
    C02_DESCRICAO = Column(String(70))


class T01tabeladcp(Base):
    __tablename__ = 't01tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t01tabeladcp_id_seq'::regclass)"))
    T01_DATA = Column(DateTime(True))
    T01_INDEXADOR = Column(String(20))
    T01_VAR_PER_MENSAL = Column(Numeric)
    T01_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T01_FATOR_VIGENTE = Column(Numeric)
    T01_INDICE_CORRECAO = Column(Numeric)


class T02tabeladcp(Base):
    __tablename__ = 't02tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t02tabeladcp_id_seq'::regclass)"))
    T02_DATA = Column(DateTime(True))
    T02_INDEXADOR = Column(String(20))
    T02_VAR_PER_MENSAL = Column(Numeric)
    T02_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T02_FATOR_VIGENTE = Column(Numeric)
    T02_INDICE_CORRECAO = Column(Numeric)


class T03tabeladcp(Base):
    __tablename__ = 't03tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t03tabeladcp_id_seq'::regclass)"))
    T03_DATA = Column(DateTime(True))
    T03_INDEXADOR = Column(String(20))
    T03_VAR_PER_MENSAL = Column(Numeric)
    T03_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T03_FATOR_VIGENTE = Column(Numeric)
    T03_INDICE_CORRECAO = Column(Numeric)


class T04tabeladcp(Base):
    __tablename__ = 't04tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t04tabeladcp_id_seq'::regclass)"))
    T04_DATA = Column(DateTime(True))
    T04_INDEXADOR = Column(String(20))
    T04_VAR_PER_MENSAL = Column(Numeric)
    T04_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T04_FATOR_VIGENTE = Column(Numeric)
    T04_INDICE_CORRECAO = Column(Numeric)


class T05tabeladcp(Base):
    __tablename__ = 't05tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t05tabeladcp_id_seq'::regclass)"))
    T05_DATA = Column(DateTime(True))
    T05_INDEXADOR = Column(String(20))
    T05_VAR_PER_MENSAL = Column(Numeric)
    T05_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T05_FATOR_VIGENTE = Column(Numeric)
    T05_INDICE_CORRECAO = Column(Numeric)


class T06tabeladcp(Base):
    __tablename__ = 't06tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t06tabeladcp_id_seq'::regclass)"))
    T06_DATA = Column(DateTime(True))
    T06_INDEXADOR = Column(String(20))
    T06_VAR_PER_MENSAL = Column(Numeric)
    T06_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T06_FATOR_VIGENTE = Column(Numeric)
    T06_INDICE_CORRECAO = Column(Numeric)


class T07tabeladcp(Base):
    __tablename__ = 't07tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t07tabeladcp_id_seq'::regclass)"))
    T07_DATA = Column(DateTime(True))
    T07_INDEXADOR = Column(String(20))
    T07_VAR_PER_MENSAL = Column(Numeric)
    T07_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T07_FATOR_VIGENTE = Column(Numeric)
    T07_INDICE_CORRECAO = Column(Numeric)


class T08tabeladcp(Base):
    __tablename__ = 't08tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t08tabeladcp_id_seq'::regclass)"))
    T08_DATA = Column(DateTime(True))
    T08_INDEXADOR = Column(String(20))
    T08_VAR_PER_MENSAL = Column(Numeric)
    T08_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T08_FATOR_VIGENTE = Column(Numeric)
    T08_INDICE_CORRECAO = Column(Numeric)


class T09tabeladcp(Base):
    __tablename__ = 't09tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t09tabeladcp_id_seq'::regclass)"))
    T09_DATA = Column(DateTime(True))
    T09_INDEXADOR = Column(String(20))
    T09_VAR_PER_MENSAL = Column(Numeric)
    T09_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T09_FATOR_VIGENTE = Column(Numeric)
    T09_INDICE_CORRECAO = Column(Numeric)


class T10tabeladcp(Base):
    __tablename__ = 't10tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t10tabeladcp_id_seq'::regclass)"))
    T10_DATA = Column(DateTime(True))
    T10_INDEXADOR = Column(String(20))
    T10_VAR_PER_MENSAL = Column(Numeric)
    T10_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T10_FATOR_VIGENTE = Column(Numeric)
    T10_INDICE_CORRECAO = Column(Numeric)


class T11tabeladcp(Base):
    __tablename__ = 't11tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t11tabeladcp_id_seq'::regclass)"))
    T11_DATA = Column(DateTime(True))
    T11_INDEXADOR = Column(String(20))
    T11_VAR_PER_MENSAL = Column(Numeric)
    T11_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T11_FATOR_VIGENTE = Column(Numeric)
    T11_INDICE_CORRECAO = Column(Numeric)


class T12tabeladcp(Base):
    __tablename__ = 't12tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t12tabeladcp_id_seq'::regclass)"))
    T12_DATA = Column(DateTime(True))
    T12_INDEXADOR = Column(String(20))
    T12_VAR_PER_MENSAL = Column(Numeric)
    T12_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T12_FATOR_VIGENTE = Column(Numeric)
    T12_INDICE_CORRECAO = Column(Numeric)


class T13tabeladcp(Base):
    __tablename__ = 't13tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t13tabeladcp_id_seq'::regclass)"))
    T13_DATA = Column(DateTime(True))
    T13_INDEXADOR = Column(String(20))
    T13_VAR_PER_MENSAL = Column(Numeric)
    T13_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T13_FATOR_VIGENTE = Column(Numeric)
    T13_INDICE_CORRECAO = Column(Numeric)


class T14tabeladcp(Base):
    __tablename__ = 't14tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t14tabeladcp_id_seq'::regclass)"))
    T14_DATA = Column(DateTime(True))
    T14_INDEXADOR = Column(String(20))
    T14_VAR_PER_MENSAL = Column(Numeric)
    T14_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T14_FATOR_VIGENTE = Column(Numeric)
    T14_INDICE_CORRECAO = Column(Numeric)


class T15tabeladcp(Base):
    __tablename__ = 't15tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t15tabeladcp_id_seq'::regclass)"))
    T15_DATA = Column(DateTime(True))
    T15_INDEXADOR = Column(String(20))
    T15_VAR_PER_MENSAL = Column(Numeric)
    T15_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T15_FATOR_VIGENTE = Column(Numeric)
    T15_INDICE_CORRECAO = Column(Numeric)


class T16tabeladcp(Base):
    __tablename__ = 't16tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t16tabeladcp_id_seq'::regclass)"))
    T16_DATA = Column(DateTime(True))
    T16_INDEXADOR = Column(String(20))
    T16_META_SELIC = Column(Numeric)
    T16_TAXA_MENSAL = Column(Numeric)


class T17tabeladcp(Base):
    __tablename__ = 't17tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t17tabeladcp_id_seq'::regclass)"))
    T17_DATA = Column(DateTime(True))
    T17_INDEXADOR = Column(String(20))
    T17_X1 = Column(Numeric)
    T17_X2 = Column(Numeric)
    T17_X3 = Column(Numeric)
    T17_X4 = Column(Numeric)
    T17_X5 = Column(Numeric)


class T18tabeladcp(Base):
    __tablename__ = 't18tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t18tabeladcp_id_seq'::regclass)"))
    T17_DATA = Column(DateTime(True))
    T17_INDEXADOR = Column(String(20))
    T18_X1 = Column(Numeric)
    T18_X2 = Column(Numeric)
    T18_X3 = Column(Numeric)
    T18_X4 = Column(Numeric)
    T18_X5 = Column(Numeric)


class T19tabeladcp(Base):
    __tablename__ = 't19tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t19tabeladcp_id_seq'::regclass)"))
    T19_DATA = Column(DateTime(True))
    T19_INDEXADOR = Column(String(20))
    T19_INDICE_CORRECAO = Column(Numeric)


class T20tabeladcp(Base):
    __tablename__ = 't20tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t20tabeladcp_id_seq'::regclass)"))
    T20_ORDEM = Column(Integer)
    T20_VIGENCIA = Column(String(30))
    T20_MOEDA = Column(String(30))
    T20_ALTERACAO = Column(String(250))
    T20_LEGISLACAO = Column(String(250))


class T21tabeladcp(Base):
    __tablename__ = 't21tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t21tabeladcp_id_seq'::regclass)"))
    T21_DATA = Column(DateTime(True))
    T21_INDEXADOR = Column(String(20))
    T21_VAR_PER_MENSAL = Column(Numeric)
    T21_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T21_FATOR_VIGENTE = Column(Numeric)
    T21_INDICE_CORRECAO = Column(Numeric)


class T22tabeladcp(Base):
    __tablename__ = 't22tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t22tabeladcp_id_seq'::regclass)"))
    T22_DATA = Column(DateTime(True))
    T22_INDEXADOR = Column(String(20))
    T22_VAR_PER_MENSAL = Column(Numeric)
    T22_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T22_FATOR_VIGENTE = Column(Numeric)
    T22_INDICE_CORRECAO = Column(Numeric)


class T23tabeladcp(Base):
    __tablename__ = 't23tabeladcp'

    id = Column(BigInteger, primary_key=True, server_default=text("nextval('acd_lst_t23tabeladcp_id_seq'::regclass)"))
    T23_DATA = Column(DateTime(True))
    T23_INDEXADOR = Column(String(20))
    T23_VAR_PER_MENSAL = Column(Numeric)
    T23_NUM_INDICE_VAR_MENSAL = Column(Numeric)
    T23_FATOR_VIGENTE = Column(Numeric)
    T23_INDICE_CORRECAO = Column(Numeric)
