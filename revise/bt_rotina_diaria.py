from bt_data_tools import ler_data_arquivo, gravar_data_arquivo, verificar_quinzena, mesmo_mes
from bt_obter_datas_ultimos_registros import *
from bt_marcar_tabelas_para_atualizacao import *

from bt_buscar_indexadores import *
from bt_atualizar_indexadores import *
from bt_conf_debug import *

''' Este módulo é executado todo dia às 8h00.
    Verifica em logatualizacao se ha na coluna processar valor = 1.
    Se houver, vai atualizar esse indice para a data do mes subsequente.
    Assim, se a coluna processar tiver valor 1 e a data 01/04/2023, 
    esse indexador sera atualizado para 01/05/2023.
'''


data_atual = dia_de_hoje()
linha_dupla = ("="*60) 
#data_inicial_indexador = formatar_data_inicio_mes(data_atual)
#data_final_indexador = incrementa_mes_str(data_inicial_indexador)

print("="*20+" LOG DE EVENTOS "+"="*24)
print(f"data_atual: {formatar_data_dmy(data_atual)}")
print(linha_dupla)


obter_as_datas_ultimos_registros()

marcar_tabelas_para_atualizacao(data_atual)

# obter os indexadores do mes que precisam ser atualizados
indexadores_do_mes, data_busca, data_retorno = buscar_indexadores()


if indexadores_do_mes:
    print(f"data_busca:{data_busca}\ndata_retorno:{data_retorno}")
    print(f"indexadores_do_mes: {indexadores_do_mes}")    
    #atualizadas = atualizar_indexadores(indexadores_do_mes,data_busca,data_retorno)










#if atualizadas:
#    print("Indexadores atualizados:")
#    for item in atualizadas:
#        print(f"{item[0]}:  {item[1]} valor: {item[2]}")




"""
if not existe_arquivo(nome_arquivo):
    gravar_data_arquivo(nome_arquivo, data_atual)

data_arquivo = ler_data_arquivo(nome_arquivo)


print("============================")

if data_arquivo is None: 
    print("arquivo não encontrado.")
else:
    print(f"data atual: {data_atual}")
    print(f"data do arquivo: {data_arquivo}")

    if mesmo_mes(data_atual, data_arquivo):
        print("não houve mudança de mês")
        print("----------------------------")
        if verificar_quinzena(data_atual):
            print("verificar atualização quinzenal - INPC/IPCA")
        #   indexadores_quinzenais=buscar_indexadores_quinzenais()
        # verificar se existem tabelas para atualizar.
    else:
        print("houve mudança de mês")
        atualizar_log_datas() # atualiza todo inicio de mês.        
        atualizar_log_processar(data_atual) # atualiza todo inicio mês
        #indexadores_do_mes = buscar_indexadores_mensais()
        indexadores_do_mes = buscar_indexadores_quinzenais()
                
        #atualizar_indexador_mensal()
        #// atualizar_tabelas_pnep()
        #gravar_data_arquivo(nome_arquivo, data_atual)

print("============================")
"""

#indexadores_do_mes = buscar_indexadores_mensais()



''' Atualizacao das tabelas de indexadores (1xx) 

1.verificar as datas das tabelas que devem ter o indice atualizado para o mes seguinte, 
ou seja, com o valor do campo processar igual a 1.

2. aqui tambem deve-se verificar se o indice eh quinzenal ou mensal.

3. buscar os indices para cada data

4. atualizar a tabela com esse novo indice.
buscar_indexadores_mensais()'''






""" Atualizacao das tabelas pnep (2xx)"""
# verificar as datas das tabelas que devem ter o indice atualizado para o mes seguinte, 
# ou seja, com o valor do campo processar igual a 1.
# aqui tambem deve-se verificar se o indice eh quinzenal ou mensal.

# buscar os indices para cada data

# atualizar a tabela com esse novo indice. 












'''                                       
            nome_tabela = obter_nome_tabela(registro[0], query13)
                        
            #pos=inserir_indice_bcb(dt_formatada, index_valor, query12, nome_tabela)
            

            if codigo_index: #pos:            
                print("------------------------------------------------------------")
                print(nome_tabela, "valor: ", index_valor, "data: ", dt_formatada)
                #resetar_flag_processar(registro[0],dt_formatada,query14)
                print("zerar o campo processar da tabela logatualizacao ")
                print("------------------------------------------------------------")
            
'''