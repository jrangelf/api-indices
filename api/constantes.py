from decouple import config, Csv

# Dados conexão postgres
SQLALCHEMY_DATABASE_URL = config('SQLALCHEMY_DB_URL')

NOREGS='Não há registro'


# Rótulos FastAPI
METANOME1 = "Índices - Débito"
METADESC1 = "Tabelas de índices PNRJ de débitos."

METANOME2 = "Índices - Crédito"
METADESC2 = "Tabelas de índices PNRJ de créditos."

METANOME3 = "Taxas de Juros - Débitos"
METADESC3 = "Taxas de juros utilizadas nos débitos"

METANOME4 = "Taxas de Juros - Créditos"
METADESC4 = "Taxas de juros utilizadas nos créditos"

METANOME5 = "Indexadores BCB"
METADESC5 = "Consulta de indexadores do Banco Central"

METANOME6 = "Controle"
METADESC6 = "Tabelas para controle e verificação da API"

TITULO = "API de Índices e Taxas de Juros - PNRJ"
DESCRICAO = "API para consulta dos índices utilizados pela Procuradoria Nacional de Riscos Judiciais da Advocacia-Geral da União"
VERSAO = "1.0"


# tags
TAGDBT = [METANOME1] 
TAGCRE = [METANOME2]

TAGJDEB = [METANOME3]
TAGJCRE = [METANOME4]

TAGIDX = [METANOME5]
TAGCRL = [METANOME6]


# tabelas de débito
T200 = 'Tabela c.m. cond. geral IPCA-E'
T202 = 'IPCA-E EC 113-2021-Nova-CJF'
T204 = 'IPCA-E + SELIC 2003-2009'
T206 = 'TR DEZ/2013 - IPCA-E JAN/2014 - SELIC'
T208 = 'IPCA-E + SELIC 2003-2009 - EC113'
T210 = 'TR DEZ/2013 - IPCA-E JAN/2014'
T212 = 'Tabela c.m. desapropriação'
T214 = 'Tabela c.m.TR_jul2009 em diante'
T216 = 'TR + SELIC 2003-2009'
T218 = 'Tabela c.m. cond.geral TR SET/2017'
T220 = 'TR FEV/91 em diante'
T222 = 'Tabela c.m. benef. INPC'
T224 = 'Tabela IGP-M FGV'
T226 = 'Tabela c.m. INPC'
T228 = 'Tabela c.m. benef. TR mar/2015'
T230 = 'TR até mar/2015'
T232 = 'TR até mar/2015 + SELIC 2003-2009'
T234 = 'TR até set/2017 + SELIC 2003-2009'
T236 = 'Tabela c.m. INPC + IPCA-E'
T238 = 'Tabela c.m. IPCA'

T240 = 'EC136 Tabela c.m. cond. geral'
T242 = 'EC136 IPCA-E + SELIC 2003-2009'
T244 = 'EC136 TR até mar/2015'
T246 = 'EC136 TR até mar/2015 + SELIC 2003-2009'
T248 = 'EC136 Tabela c.m. TR jul/2009'
T250 = 'EC136 TR + SELIC 2003-2009'
T252 = 'EC136 TR set/2017'
T254 = 'EC136 TR set/2017 + SELIC 2003-2009'
T256 = 'EC136 TR dez/2013 IPCA-E jan/2014'
T258 = 'EC136 TR dez/2013 IPCA-E jan/2014 SELIC'
T260 = 'EC136 TR fev/91 em diante'
T262 = 'EC136 Tabela desapropriação'
T264 = 'EC136 Tabela c.m. INPC'
T266 = 'EC136 Tabela c.m. INPC + IPCA-E'
T268 = 'EC136 Tabela c.m. benef. INPC'
T270 = 'EC136 Tabela c.m. benef. TR mar/2015'

# tabelas de crédito
T400 = 'Tabela c.m. IPCA-E'
T402 = 'Tabela IPCA-E EC 113-21'
T404 = 'Tabela TR set-2017-Créditos'
T406 = 'Tabela c.m. INPC'
T408 = 'Tabela c.m. IPCA'
T410 = 'EC136 Tabela c.m. IPCA-E'
T412 = 'EC136 Tabela TR set-2017-Créditos'
T414 = 'EC136 Tabela c.m. INPC'
T416 = 'EC136 Tabela c.m. SELIC 2003'

# tabelas de juros débito
T300 = 'Juros poupança'
T302 = 'Juros 0,5% até junho de 2009'
T304 = 'Juros 0,5% - Selic 2003-2009 - Poupança'
T306 = 'Juros 1% até julho 2001'
T308 = 'Juros 0,5% - poupança - EC 113-2021'
T310 = 'Juros 1% até julho 2001 EC113-2021'
T312 = 'SELIC - EC 113-2021'
T314 = 'Juros Taxa Legal'
T316 = 'Juros Taxa Legal - Ben.Previdenciário'
TPNN = 'Tabela exclusiva da calculadora PNN'

# tabelas de juros crédito
T322 = 'Juros 0,5%-Poupança'
T324 = 'Juros 0,5%-Poupança-EC 113-2021'
T326 = 'Juros 1%'
T328 = 'Juros 1% EC113-2021'
T330 = 'Juros 0,5% até dez/2002'
T332 = 'SELIC - 2003 em diante'
T334 = 'SELIC - EC 113-2021'
T336 = 'Juros Taxa Legal'
T338 = 'Juros Taxa Legal - Ben.Previdenciário'
T340 = 'Juros 0,5% - SELIC - Taxa Legal'

# indexadores do banco central
T100 = 'Tabela INPC'
T102 = 'Tabela IPCA'
T104 = 'Tabela TR'
T107 = 'SELIC acumulada até a data {mes}/{ano}'
T106 = 'Tabela SELIC'
T108 = 'Tabela SELIC Copom'
T110 = 'Tabela IPCA-15'
T112 = 'Tabela IGP-M'
T114 = 'Tabela Juros Taxa Legal'