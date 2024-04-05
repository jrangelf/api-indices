
from bt_queries import *
from bt_database import *
from bt_marcar_tabelas_para_atualizacao import *
#from datetime import datetime
from revise.bz_atualizar_indexador_quinzenal import *
from revise.bz_buscar_indexadores_mensais import *
from bt_consulta_bcb_indexadores import *
#from bt_data_tools import incrementa_mes

data_atual = dia_de_hoje() 
data_inicial_indexador = formatar_data_inicio_mes(data_atual)
data_final_indexador = incrementa_mes_str(data_inicial_indexador)

print(f"\ndata_atual: {formatar_data_dmy(data_atual)}\n")
print(f"indexador:\n  -data_inicial: {data_inicial_indexador}")
print(f"  -data_final: {data_final_indexador}")
print("============================================================")

data_inicial = "01/02/2024" #data_inicial_indexador 
data_final = "01/03/2024" #data_final_indexador 


indexadores_do_mes =[]

#indexes2 = buscar_codigo_bcb_indexadores()
#print(f"indexes2: \n{indexes2}")
#indexes = {'selic':4390,'tr':226, 'ipca':433, 'ipca15':7478, 'inpc':188, 'selic_copom':432}

indexes = buscar_codigo_bcb_indexadores()

while indexes:

    print(indexes)
    
    for indexador, codigo in indexes.copy().items():
        resposta = consultar_bc_periodo(codigo, data_inicial, data_final)
        if resposta:
            if indexador == 'TR':
                for i in resposta:
                    if i['data']==data_inicial and i['datafim'] == data_final:
                        valor = i['valor']
                        # por conta de ser a TR, colocar data = data_inicial
                        #data = i['datafim']
                        data = i['data']
                        del indexes[indexador]
                        
                        
            
            else:
                valor = resposta[0]['valor']
                data = resposta[0]['data']
                del indexes[indexador]
            
            indexadores_do_mes.append([indexador, data, valor])
        

print(f"\nIndexadores do mês:")
for item in indexadores_do_mes:
    print(f"{item[0]}:  {item[1]} valor: {item[2]}")

#consulta_selic_receita()

