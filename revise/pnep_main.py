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
tabelas=indexadores.atualizar_indexadores()
if tabelas:
    print('...')
else:
    print('Nao ha tabelas de indexadores para atualizar.')
    
indices = Indices()
indices.atualizar_indices()





