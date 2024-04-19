from pnep_queries import QueriesSQL
from pnep_conexao import Database
from pnep_date_tools import DateTools
from pnep_tabelas import Tabelas
from pnep_api_bcb import ApiBcb
from pnep_sqldata import SQLData
from pnep_indexadores import Indexadores
from pnep_indices import Indices

queries = QueriesSQL()
conexao = Database().conectar()
datetools = DateTools()

sqldata = SQLData(queries=queries, datetools=datetools, conexao=conexao)
tabelas = Tabelas(sqldata=sqldata)
apibcb = ApiBcb()


indexadores = Indexadores(datetools=datetools, tabelas=tabelas, apibcb=apibcb)
tabelas_bcb = indexadores.atualizar_indexadores()
if not tabelas_bcb:
    print('Nao ha tabelas de indexadores do BCB para atualizar.')
    


indices = Indices()
tabelas_pnep = indices.atualizar_indices()
if tabelas_pnep:
    print(tabelas_pnep)
else:
    print('Nao ha tabelas de indices_pnep para atualizar')





