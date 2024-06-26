
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
    
    def buscar_indexadores(self, registros):        
        self.registros = registros        
        indexadores_do_mes = []
        if self.registros:            
            # seleciona o codigo bcb dos indexadores     
            lista = self.tabelas.buscar_codigo_bcb_indexadores(registros)
            
            ''' Da lista = [(104, '01/02/2024', 'tr', 8, '226'), (112, '01/02/2024', 'igpm', 12, '189')]
            Gerar um dicionario indexes = {'TR': ('01/02/2024', '226'), 'IGPM': ('01/02/2024', '189')} '''
            
            indexes = {item[2].upper(): (item[1], item[4]) for item in lista}            
            
            while indexes:                            
                for indexador, tupla in indexes.copy().items():
                    data_inicial = tupla[0]
                    codigo = tupla[1]

                    # TR: dt_ini = dt_inicial do mes seguinte e a dt_final = dt_ini incrementada de um mes
                    if indexador == 'TR':
                        nova_data_inicial = self.datetools.incrementa_mes_str(data_inicial)
                        nova_data_final = self.datetools.incrementa_mes_str(nova_data_inicial)                    
                        data_inicial = nova_data_inicial
                        data_final = nova_data_final
                    else:
                        data_inicial = self.datetools.incrementa_mes_str(data_inicial)
                        data_final = data_inicial
                    
                    resposta = self.apibcb.consultar_bc_periodo(codigo, data_inicial, data_final)
                    if resposta:
                        if indexador == 'TR':
                            for i in resposta:
                                if i['data']==data_inicial and i['datafim'] == data_final:
                                    valor = i['valor']                                    
                                    data = i['data']
                                    del indexes[indexador]                      
                        else:
                            valor = resposta[0]['valor']
                            data = resposta[0]['data']
                            del indexes[indexador]
                                                                       
                        indexadores_do_mes.append([indexador, data, valor, data_inicial])        
        return indexadores_do_mes, lista
    
    def inserir_novos_indexadores(self, indexadores, lista):

        ''' lista: [(102, '01/11/2023', 'ipca', 6, '433'), 
                    (104, '01/02/2024', 'tr', 8, '226'), 
                    (112, '01/02/2024', 'igpm', 12, '189')]
            
            indexadores = [['IPCA', '01/12/2023', '0.56', '01/12/2023'], 
                           ['IGPM', '01/03/2024', '-0.47', '01/03/2024'], 
                           ['TR', '01/03/2024', '0.0331', '01/03/2024'], 
                           ['SELIC', '01/02/2024', '0.33', '01/03/2024']]
            
            caso as datas indexadores[i][1] == indexadores[i][3] gerar uma sublista

            sublista = [['IPCA', '01/12/2023', '0.56'], ['IGPM', '01/03/2024', '-0.47'], ['TR', '01/03/2024', '0.0331']]
            
            lista_atualizacao = ['IPCA', '01/12/2023', '0.56', 102], 
                                ['IGPM', '01/03/2024', '-0.47', 112], 
                                ['TR', '01/03/2024', '0.0331', 104] '''
        
        sublista = [sub_lista[:3] for sub_lista in indexadores if sub_lista[1] == sub_lista[3]]

        lista_atualizacao = []
        for item_sub in sublista:    
            for item_lista in lista:        
                if item_sub[0].lower() in item_lista:
                    lista_atualizacao.append([item_sub[0],item_sub[1],item_sub[2],item_lista[0]])

        tabelas_indexador_atualizadas =[]
        if lista_atualizacao:
            for registro in lista_atualizacao:
                nome_indexador = registro[0]
                tabela = nome_indexador.lower()
                dt_formatada = self.datetools.formatar_dmy_para_ymd(registro[1])        
                valor = registro[2]
                codigotab = registro[3]                
                indice_inserido=self.tabelas.inserir_indice_bcb(dt_formatada, valor, tabela)                    
                if indice_inserido:
                    tabelas_indexador_atualizadas.append(indice_inserido)
                    self.tabelas.zerar_processar(codigotab,dt_formatada)
            return tabelas_indexador_atualizadas
        return None

    def atualizar_indexadores(self):       
        print("\n")
        print("="*20+" LOG DE EVENTOS "+"="*24)
        print(f"{self.datetools.dia_de_hoje().strftime('%d/%m/%Y %H:%M:%S')}\n")       
        
        ''' tabela_codigo_data_indexador eh uma lista de tuplas com as datas de atualizacao das tabelas
            [('inpc', 100, '2024-03-01', 7),...] '''        
        tabela_codigo_data_indexador = self.tabelas.obter_datas_atualizacao_tabelas()
        

        ''' _registros recebe uma lista de tuplas com nome da tabela e o ultimo registro de data de cada
            tabela atualizada em logatualizacao
            registros = [('inpc', '2024-03-01'), 
                         ('ipca', '2024-03-01'), ... , 
                         ('t202_tabela_pnep', '2021-12-01')] '''
        _registros = self.tabelas.atualizar_datas_logatualizacao(tabela_codigo_data_indexador)
        
        # marcar tabelas para atualizacao        
        tabelas_marcadas_atualizacao = self.tabelas.marcar_tabelas_para_atualizacao(self.datetools.dia_de_hoje())        
        
        if tabelas_marcadas_atualizacao:
            # incluir dois registros em cada tupla da lista (nome da tabela e codigo do indexador)
            tab_marcadas_merge = Indexadores.agregar(tabela_codigo_data_indexador,
                                                     tabelas_marcadas_atualizacao)
            if tab_marcadas_merge:
                # retirar da lista de tabelas_para_processar as tabelas que nao sao de indexadores
                filtrar_tabelas_indexadores = [tupla for tupla in tab_marcadas_merge if tupla[0] < 200]
                
                if filtrar_tabelas_indexadores:
                    print(f'Tabelas de indexadores para atualizar:')
                    for registro in filtrar_tabelas_indexadores:
                        print(registro)                     

                    # obter os indexadores do mes que precisam ser atualizados
                    indexadores_do_mes, lista = self.buscar_indexadores(filtrar_tabelas_indexadores)

                    if indexadores_do_mes:
                        # indexadores_do_mes = [indexador, data retorno, valor, data busca']                       
                        atualizados = self.inserir_novos_indexadores(indexadores_do_mes,lista)

                        if atualizados:
                            for registro in atualizados:
                                print(f"{registro}")                        
                            return atualizados                                            
        return None        

    
    
    


    
