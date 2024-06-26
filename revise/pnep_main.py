from pnep_queries import QueriesSQL
from pnep_conexao import Database
from pnep_date_tools import DateTools
from pnep_tabelas import Tabelas
from pnep_api_bcb import ApiBcb
from pnep_api_index import ApiIndex
from pnep_sqldata import SQLData
from pnep_indexadores import Indexadores
from pnep_indices import Indices
from pnep_juros import Juros

queries = QueriesSQL()
conexao = Database().conectar()
datetools = DateTools()

sqldata = SQLData(queries=queries, datetools=datetools, conexao=conexao)
tabelas = Tabelas(sqldata=sqldata)
apibcb = ApiBcb()
apiindex = ApiIndex()


indexadores = Indexadores(datetools=datetools, tabelas=tabelas, apibcb=apibcb)
tabelas_bcb = indexadores.atualizar_indexadores()    

indices = Indices(datetools=datetools, tabelas=tabelas, apiindex=apiindex)
tabelas_pnep = indices.atualizar_indices()

juros = Juros(datetools=datetools, tabelas=tabelas, apiindex=apiindex)
tabelas_juros = juros.atualizar_juros()






