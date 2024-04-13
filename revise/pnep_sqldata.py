class SQLData:

    '''classe responsavel por toda requisicao com o banco de dados
        os metodos da classe Tabela fazerm uso dos metodos'''

    def __init__(self, queries, datetools, conexao):
        self.queries = queries
        self.datetools = datetools
        self.conexao = conexao 
        self.cursor = self.conexao.cursor()    
    
    def selecionar_multiplos(self, query):
        lista = []
        if self.cursor is not None:           
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            for row in rows:
                lista.append(row)        
            return lista
        return None
    
    def selecionar_multiplos_raw(self, query):        
        if self.cursor is not None:            
            self.cursor.execute(query)
            rows = self.cursor.fetchall()            
            return rows             
        return None
    
    def selecionar_indices_precisam_atualizacao(self):        
        registros = self.selecionar_multiplos(self.queries.consulta_4)
        return registros    

    def buscar_nome_e_codigo_das_tabelas(self):
        registros = self.selecionar_multiplos_raw(self.queries.consulta_1)
        return registros        
        
    def seleciona_ultima_data_das_tabelas(self,registros):
        # seleciona a ultima data de cada tabela retornando uma lista que contem
        # o nome da tabela, codigo da tabela, data do ultimo registro e o codigo do indexador
        lista = []        
        if self.cursor is not None:            
            for registro in registros:                
                consulta_substituida = self.queries.consulta_2.replace('$', registro[0])
                self.cursor.execute(consulta_substituida)
                row = self.cursor.fetchone()                
                lista.append((registro[0], registro[1], row[0], registro[2]))                
            return lista
        return None    
    
    def update_processar_logatualizacao(self, lista, data_atual, query):
        tabelas_para_processar = []        
        if self.cursor is not None:            
            for codigo, data_log in lista:                
                if self.datetools.verificar_data_atualizacao(codigo, data_atual, data_log):
                    query_substituida = query.replace('$', str(codigo))                
                    self.cursor.execute(query_substituida)
                    tabelas_para_processar.append((codigo, data_log.strftime("%d/%m/%Y") ))                    
            self.conexao.commit()
        return tabelas_para_processar    
    
    def atualizar_datas_logatualizacao(self,tupla):
        ''' atualiza as datas de atualizacao da tabela logatualizacao '''    
        datas_tab_logatualizacao_atualizadas = []        
        if self.cursor is not None:
            for tabela, codigo, data, indexador in tupla:

                #print(f"tabela:{tabela} codigo:{codigo} data:{data} indexador:{indexador}")
                #print("=============================================")
                #print("data_atualizacao (logatualizacao) atualizada ")
                
                # converter a data -> data.strftime("%Y-%m-%d")
                data_formatada = self.datetools.formatar_data_str_ymd(data) 
                try:
                    substituida = self.queries.consulta_3.replace('$1', data_formatada).replace('$2', str(codigo))            
                    self.cursor.execute(substituida)
                    datas_tab_logatualizacao_atualizadas.append((tabela, data_formatada))                
                    self.conexao.commit()
                except Exception as e:                    
                    return f"Erro ao executar query para {tabela}\n{substituida}\nErro:{e}"
                
            print(f"datas_tab_log: {datas_tab_logatualizacao_atualizadas}")                            
            return datas_tab_logatualizacao_atualizadas                                        
        return None
    

    def indicar_tabelas_para_atualizacao(self, data_atual):        
        codigos_datas = self.selecionar_multiplos(self.queries.consulta_5)
        tabelas_para_processar = self.update_processar_logatualizacao(codigos_datas, 
                                                                      data_atual, 
                                                                      self.queries.atualizacao_1) 
        
        print(f"SQLData:TABELAS PARA PROCESSAR:\n{tabelas_para_processar}")
        
        return tabelas_para_processar
    
        

    
    

