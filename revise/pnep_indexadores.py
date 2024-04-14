
class Indexadores:

    def __init__(self, datetools, tabelas, apibcb):        
        self.datetools = datetools        
        self.tabelas = tabelas
        self.apibcb = apibcb 
    
    @staticmethod
    def agregar(lista1, lista2):
        if lista1 and lista2:
            # Criando um conjunto dos segundos elementos de lista1 para verificação rápida de correspondência            
            set_lista1 = {item[1] for item in lista1}
            
            # Usando compreensão de lista para criar lista3
            lista3 = [(item2[0], item2[1], item1[0], item1[3]) 
                    for item2 in lista2 
                    for item1 in lista1 
                    if item2[0] in set_lista1 and item1[1] == item2[0]]
            
            return lista3
        return None

    # def agregar(lista1, lista2):
    #     lista3 = []
    #     for item2 in lista2:
    #         valor_lista2 = item2[0]
    #         for item1 in lista1:
    #             valor_lista1 = item1[1]
    #             if valor_lista2 == valor_lista1:
    #                 nova_tupla = (item2[0], item2[1], item1[0], item1[3])
    #                 lista3.append(nova_tupla)
    #                 break
    #     return lista3

    def buscar_indexadores(self):        
        dictregistros = {}
        indexadores_do_mes = []
        data_busca = ""
        data_retorno = ""
   
        # seleciona todos os indices que precisam ser atualizados
        #registros = self.sqldata.selecionar_multiplos(self.queries.consulta_4)
        registros = self.tabelas.selecionar_indices_precisam_atualizacao()    
    
        if registros:
            for registro in registros:
                chave = registro[0]
                data = registro[1].strftime('%d/%m/%Y')
                dictregistros[chave]=data   
            
            print (f"dict_registros: {dictregistros}")

            # seleciona todos os indices e seus respectivos codigos bc    
            indexes = self.sqldata.buscar_codigo_bcb_indexadores()  

            # Retirar as chaves do dicionário 'indexes' que não estão presentes no dicionário 'dictregistros'
            indexes = {chave: valor for chave, valor in indexes.items() if chave in dictregistros}

            while indexes:
                # deve-se verificar se o indice for a TR, bem como INPC e IPCA que tem especificidades
                print(f"indexes: {indexes}")
            
                for indexador, codigo in indexes.copy().items():
                    data_inicial = dictregistros[indexador]

                    # na TR a data_inicial sera nova_data_inicial = data_inicial do mes seguinte
                    # e a data final sera a nova_data_inicial incrementada de um mes
                
                    #print(f"data_ultimo_registro_tabela_indexadores: {data_inicial}")
                    #print(f"data_incrementada: {incrementa_mes_str(data_inicial)}")
                
                    if indexador == 'TR':
                        nova_data_inicial = self.datetools.incrementa_mes_str(data_inicial)
                        nova_data_final = self.datetools.incrementa_mes_str(nova_data_inicial)
                    
                        data_inicial = nova_data_inicial
                        data_final = nova_data_final

                    else:
                        data_inicial = self.datetools.incrementa_mes_str(data_inicial)
                        data_final = data_inicial

                    data_busca = data_inicial

                    print(f"[dt_ini_busca_bc]: {data_inicial}")
                    print(f"[dt_fin_busca_bc]: {data_final}")
                
                    resposta = self.apibcb.consultar_bc_periodo(codigo, data_inicial, data_final)
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
    
        # atualizar_indexadores
    def inserir_novos_indexadores(indexadores,data_busca, data_retorno):
    
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



    def atualizar_indexadores(self):       
        print("="*20+" LOG DE EVENTOS "+"="*24)       
        ''' obter as datas de atualizacao das tabelas
        tabela_codigo_data = [('inpc', 100), ('ipca', 102), ... , ('t202_tabela_pnep', 202)] '''
        #print('\nobter as datas de atualizacao das tabelas')
        tabela_codigo_data_indexador = self.tabelas.obter_datas_atualizacao_tabelas()        

        ''' atualizar a tabela logatualizacao com os valores dessas datas
        registros = [('inpc', '2024-03-01'), ('ipca', '2024-03-01'), ... , ('t202_tabela_pnep', '2021-12-01')] '''
        #print('atualizar o campo data de atualizacao da tabela logatualizacao')
        registros = self.tabelas.atualizar_logatualizacao(tabela_codigo_data_indexador)      
        
        '''# marcar tabelas para atualizacao '''
        #print('marcar as tabelas que devem ser atualizadas')
        tabelas_marcadas_atualizacao = self.tabelas.marcar_tabelas_para_atualizacao(self.datetools.dia_de_hoje())
        
        #print(f"lista1: {tabela_codigo_data_indexador}\n")
        print(f"lista2: {tabelas_marcadas_atualizacao}")

        tab_marcadas_atualizacao_merge = Indexadores.agregar(tabela_codigo_data_indexador,
                                                               tabelas_marcadas_atualizacao)

        print(f"lista3: {tab_marcadas_atualizacao_merge}")


        if tabelas_marcadas_atualizacao:
            # incluir dois registro em cada tupla da lista (nome da tabela e codigo do indexador)
            tab_marcadas_merge = Indexadores.agregar(tabela_codigo_data_indexador,
                                                               tabelas_marcadas_atualizacao)
            if tab_marcadas_merge:
                # retirar da lista de tabelas_para_processar as tabelas que nao sao de indexadores
                tab_proc_filtrada = [tupla for tupla in tab_marcadas_merge if tupla[0] < 200]
                
                if tab_proc_filtrada:
                    print(f'tabelas de indexadores para atualizar:')
                    for registro in tab_proc_filtrada:
                        print(registro)

                    # obter os indexadores do mes que precisam ser atualizados
                    #indexadores_do_mes, data_busca, data_retorno = buscar_indexadores()

                    #if indexadores_do_mes:
                    #    print(f"data_busca:{data_busca}\ndata_retorno:{data_retorno}")
                    #    print(f"indexadores_do_mes: {indexadores_do_mes}")    
                    #    atualizadas = atualizar_indexadores(indexadores_do_mes,data_busca,data_retorno)
                
        
        
        return None
    
    
