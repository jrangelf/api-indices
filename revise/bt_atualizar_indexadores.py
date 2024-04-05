from bt_queries import *
from bt_database import *
from bt_consulta_bcb_indexadores import *
from bt_data_tools import *

''' Este módulo vai atualizar os indexadores com a data do mês subsequente ao que 
    estiver indicado na tabela logatualizacao '''

def atualizar_indexadores(indexadores,data_busca, data_retorno):
    
    atualizadas = []   
    codigos = selecionar_multiplos(query17)
    codigo_dict = {codigo[0]: codigo[1] for codigo in codigos}

    print(f"codigo_dict: {codigo_dict}")
    print(f"indexadores: {indexadores}")

    for indexador in indexadores:
        nome_indexador = indexador[0]
        tabela = codigo_dict.get(nome_indexador)
        
        dt_formatada = formatar_dmy_para_ymd(indexador[1])        
        valor = indexador[2]

        codigotab = obter_codigo_tabela(tabela,query18)

        print(f"{tabela} ({codigotab})  {dt_formatada} {valor}")        

        print(f"data_para_inserir_tabela_indexador:{dt_formatada}")

        if data_busca == data_retorno:
            pos=inserir_indice_bcb(dt_formatada, valor, query12, tabela)
            
            if pos:
                atualizadas.append([indexador[0], indexador[1], indexador[2]])
                resetar_flag_processar(codigotab,dt_formatada,query14)

    return atualizadas


"""
      indexadores_do_mes.append([indexador, data, valor])
def buscar_indexadores_quinzenais():   
    
    dictregistros = {}
    indexadores_quinzenais = []
    data_atual = datetime.now()
    data_atual_formatada = data_atual.strftime("%d/%m/%Y")
    
    # seleciona todos os indices com suas respectivas ultimas data de atualizacao
    registros = selecionar_multiplos(query16)    
    for registro in registros:
        chave = registro[0]
        data = registro[1].strftime('%d/%m/%Y')
        dictregistros[chave]=data
    
    
    print (f"dictregistros: {dictregistros}")

    # seleciona todos os indices e seus respectivos codigos bcb    
    indexes = buscar_codigo_bcb_indexadores()  
    
    chaves_para_excluir = [chave for chave in indexes if chave not in ['IPCA', 'INPC']]
    for chave in chaves_para_excluir:
        del indexes[chave]

    while indexes:
        print(f"indexes: {indexes}")           
        for indexador, codigo in indexes.copy().items():
            if indexador in dictregistros:
                data_inicial = dictregistros[indexador]
            else:
                data_inicial = data_atual_formatada
            
            data_inicial = incrementa_mes_str(data_inicial)
            data_final = data_inicial
            
            resposta = consultar_bc_periodo(codigo, data_inicial, data_final)
            if resposta:
                valor = resposta[0]['valor']
                data = resposta[0]['data']
                del indexes[indexador]                   
                indexadores_quinzenais.append([indexador, data, valor])

    return indexadores_quinzenais

"""
        