from bt_queries import *
from bt_database import *
from bt_consulta_bcb_indexadores import *
from bt_data_tools import *

''' Este módulo vai buscar todos indexadores do Banco Central utilizando como data
    de busca a data do mês subsequente ao que estiver indicado na tabela logatualizacao '''

def buscar_indexadores():   
    
    dictregistros = {}
    indexadores_do_mes = []
    data_busca = ""
    data_retorno = "" 
   
    # seleciona todos os indices que precisam ser atualizados
    registros = selecionar_multiplos(query16)    
    
    if registros:

        for registro in registros:
            chave = registro[0]
            data = registro[1].strftime('%d/%m/%Y')
            dictregistros[chave]=data   
        
        print (f"dict_registros: {dictregistros}")

        # seleciona todos os indices e seus respectivos codigos bc    
        indexes = buscar_codigo_bcb_indexadores()
        print(f"indexes: {indexes}")  

        # Retirar as chaves do dicionário 'indexes' que não estão presentes no dicionário 'dictregistros'
        indexes = {chave: valor for chave, valor in indexes.items() if chave in dictregistros}

        while indexes:

            # deve-se verificar se o indice for a TR, bem como INPC e IPCA que tem especificidades

            print(f"indexes: {indexes}")
            
            for indexador, codigo in indexes.copy().items():
                data_inicial = dictregistros[indexador]

                # na TR a dt_inicial sera nova_data_inicial = data_inicial do mes seguinte
                # e a data final sera a nova_data_inicial incrementada de um mes
            
                #print(f"data_ultimo_registro_tabela_indexadores: {data_inicial}")
                #print(f"data_incrementada: {incrementa_mes_str(data_inicial)}")
            
                if indexador == 'TR':
                    nova_data_inicial = incrementa_mes_str(data_inicial)
                    nova_data_final = incrementa_mes_str(nova_data_inicial)
                
                    data_inicial = nova_data_inicial
                    data_final = nova_data_final

                else:
                    data_inicial = incrementa_mes_str(data_inicial)
                    data_final = data_inicial

                data_busca = data_inicial

                print(f"[dt_ini_busca_bc]: {data_inicial}")
                print(f"[dt_fin_busca_bc]: {data_final}")

            
                resposta = consultar_bc_periodo(codigo, data_inicial, data_final)
                if resposta:
                    if indexador == 'TR':
                        for i in resposta:
                            if i['data']==data_inicial and i['datafim'] == data_final:
                                valor = i['valor']
                                #data = i['datafim']
                                data = i['data']
                                del indexes[indexador]
                    
                    else:
                        valor = resposta[0]['valor']
                        data = resposta[0]['data']
                        del indexes[indexador]

                    data_retorno = data
                
                    print(f"data_inicial_retorno_bc: {data_inicial}")
                    print(f"data_final_retorno_bc: {data_retorno}")
                    
                    indexadores_do_mes.append([indexador, data, valor])

    return indexadores_do_mes, data_busca, data_retorno


