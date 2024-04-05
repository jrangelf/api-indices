from bt_database import *
from bt_data_tools import converter_data_para_str

''' Este módulo vai verificar em cada tabela de indexadores e em cada tabela de índices-pnep 
    a data do último registro inserido. 
    Em seguida vai inserir no campo data_atualizacao da tabela logatualizacao o valor da data 
    desse último registro em cada tabela relacionada com a data respectiva.
    Isso garante que todas as tabelas serão atualizadas apenas com o indexador do mês imediatamente 
    seguinte, evitando que haja saltos em algum mês.   
'''

def obter_as_datas_ultimos_registros(): 
    print(f"----------------------------------\nobter_as_datas_ultimos_registros()\n----------------------------------")   
    tabelas = selecionar_tabelas(query0) # seleciona todas as tabelas (index e indices)
    
    ''' tabelas, codigos = buscar_nome_e_codigo_das_tabelas(query0)'''
    
    print(f"tabelas:\n{tabelas}")
    
    datas = seleciona_ultima_data_das_tabelas(tabelas,query3) # seleciona as datas dos últimos registros
    
    ''' datas = buscar_data_ultimo_registro_tabelas(tabelas,query3)'''

    print(f"datas:\n{datas}")
    codigos = selecionar_codigos_tabelas(datas,query4) # seleciona os códigos das tabelas
    print(codigos)
    for i in codigos:
        print(f"{i[0]}:  {i[1]}  {converter_data_para_str(i[2])}")
    
    # atualiza a tabela logatualizacao com a ultima data de cada tabela de indexadores
    update_datas_logatualizacao(codigos, query6) # UPDATE logatualizacao SET data_atualizacao='$1' WHERE codigo_tabela=$2     
    
    ''' atualizar_datas_em_logatualizacao(codigos,query6)'''
    
    return None

    
    
    
    
    
