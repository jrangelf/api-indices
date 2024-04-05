
from pnep_queries import QueriesSQL
from pnep_verificacao import VerificacaoTabelas
from pnep_sqldata import SQLData
from pnep_conexao import conectar_db
from pnep_date_tools import DateTools


queries = QueriesSQL()
datetools = DateTools()
sqldata = SQLData(conexao=conectar_db, queries_sql=queries, datetools=datetools) 
verificacao = VerificacaoTabelas(sqldata)

# obtem as datas de atualizacao das tabelas
tabela_codigo_data = verificacao.obter_datas_atualizacao_tabelas()

#for registro in tabela_codigo_data:
#    print(f"tabela:{registro[0]} codigo:{registro[1]} data:{registro[2]}")

# atualizar a tabela logatualizacao com os valores dessas datas
registros = verificacao.atualizar_logatualizacao(tabela_codigo_data)

print (registros)
print(DateTools.dia_de_hoje())

# marcar tabelas para atualizacao
#tabelas_marcadas_atualizacao = verificacao.marcar_tabelas_para_atualizacao(tabela_codigo_data)




















