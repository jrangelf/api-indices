class SQLData:

    '''classe responsavel por toda requisicao com o banco de dados
        os metodos da classe Tabela recebem por injecao de dependencia os metodos da classe SQLData'''
    
    def __init__(self, queries, datetools, conexao):
        self.queries = queries
        self.datetools = datetools
        self.conexao = conexao 
        self.cursor = self.conexao.cursor()
    
    def selecionar_multiplos(self, query):
        lista = []
        try:
            if self.cursor is not None:           
                self.conexao.commit()
                self.cursor.execute(query)
                rows = self.cursor.fetchall()
                self.conexao.commit()
                for row in rows:
                    lista.append(row)
                return lista
        except Exception as e:
            self.conexao.rollback()            
            print(f"\nErro ao executar a consulta: {e}\n({query})\n")
            return None
    
    def selecionar_multiplos_raw(self, query):
        try:        
            if self.cursor is not None:
                self.conexao.commit()
                self.cursor.execute(query)
                rows = self.cursor.fetchall()
                self.conexao.commit()            
                return rows 
        except Exception as e:
            self.conexao.rollback()
            print(f"\nErro ao executar a consulta: {e}\n({query})\n")             
            return None
    
    def selecionar_indices_precisam_atualizacao(self):        
        registros = self.selecionar_multiplos(self.queries.consulta_4)
        return registros    

    def buscar_nome_e_codigo_das_tabelas(self):
        registros = self.selecionar_multiplos_raw(self.queries.consulta_1)
        return registros        
        
    def seleciona_ultima_data_das_tabelas(self,registros):
        # lista com nome da tabela, codigo da tabela, data do ultimo registro e o codigo do indexador
        lista = [] 
        if registros:
            try:        
                if self.cursor is not None:            
                    self.conexao.commit()
                    for registro in registros:                
                        consulta_substituida = self.queries.consulta_2.replace('$', registro[0])
                        self.cursor.execute(consulta_substituida)
                        row = self.cursor.fetchone()                
                        lista.append((registro[0], registro[1], row[0], registro[2]))                
                    self.conexao.commit()
                    return lista
            except Exception as e:
                self.conexao.rollback()
                print(f"\nErro ao executar a consulta: {e}\n({consulta_substituida})\n")             
                return None      
        return None    
    
    def atualizar_datas_logatualizacao(self,tupla):
        ''' atualiza as datas de atualizacao da tabela logatualizacao '''
        if tupla:    
            datas_tab_logatualizacao_atualizadas = []                    
            if self.cursor is not None:
                for tabela, codigo, data, _indexador in tupla:                                        
                    self.conexao.commit()
                    try:
                        # converter a data -> data.strftime("%Y-%m-%d")
                        data_formatada = self.datetools.formatar_data_str_ymd(data) 
                    except Exception as e:
                        print (f"Erro ao formatar a data: {data}\nError:{e}")
                        data_formatada =""
                        return None
                    try:
                        substituida = self.queries.consulta_3.replace('$1', data_formatada).replace('$2', str(codigo))            
                        self.cursor.execute(substituida)                        
                        self.conexao.commit()
                        datas_tab_logatualizacao_atualizadas.append((tabela, data_formatada))
                    except Exception as e:
                        substituida = ""
                        self.conexao.rollback()                    
                        print (f"Erro ao executar query para {tabela}\n{substituida}\nError:{e}")
                        return None                
                return datas_tab_logatualizacao_atualizadas                                        
        return None    
    
    def update_processar_logatualizacao(self, lista, data_atual, query):
        tabelas_para_processar = []
        try:        
            if self.cursor is not None:
                self.conexao.commit()            
                for codigo, data_log in lista:                
                    if self.datetools.verificar_data_atualizacao(codigo, data_atual, data_log):
                        query_substituida = query.replace('$', str(codigo))                
                        self.cursor.execute(query_substituida)
                        tabelas_para_processar.append((codigo, data_log.strftime("%d/%m/%Y") ))                    
                self.conexao.commit()
            return tabelas_para_processar
        except Exception as e:
            self.conexao.rollback()
            print(f"\nErro ao executar update em logatualizacao: {e}\n({query})\n")             
            return None
    
    def marcar_tabelas_para_atualizacao(self, data_atual):        
        codigos_datas = self.selecionar_multiplos(self.queries.consulta_5)
        if codigos_datas:
            tabelas_para_processar = self.update_processar_logatualizacao(codigos_datas, 
                                                                      data_atual, 
                                                                      self.queries.atualizacao_1)
            return tabelas_para_processar
        return None    
    
    def buscar_codigo_bcb_indexadores(self, registros):
        novos_regs = []        
        try:        
            self.conexao.commit()
            if self.cursor is not None:
                for reg in registros:
                    query_substituida = self.queries.consulta_6.replace('$', str(reg[3]))                
                    self.cursor.execute(query_substituida)
                    row = self.cursor.fetchone()
                    novos_regs.append((reg[0], reg[1], reg[2], reg[3], row[0]))
                self.conexao.commit()
                return novos_regs
            return None                
        except Exception as e:
            self.conexao.rollback()
            print(f"\nErro ao obter codigos bcb dos indexadores: {e}\n({query_substituida})\n")             
            return None
        
    def inserir_indice_bcb(self, data, valor, nome_tabela):
        try:
            self.conexao.commit()
            if self.cursor is not None:
                query_substituida = self.queries.insercao_1.replace('$1', str(nome_tabela)).replace('$2',data).replace('$3',str(valor))
                self.cursor.execute(query_substituida)            
                self.conexao.commit()   
                return f"[{nome_tabela.upper()}]: {data}  valor = {valor}"
            return None
        except Exception as e:
            self.conexao.rollback()
            print(f"\nErro ao inserir novo valor na tabela de indexador: {e}\n({query_substituida})\n")
            return None

    def zerar_processar(self,codigo, data):
        try:
            if self.cursor is not None:
                query_substituida = self.queries.atualizacao_2.replace('$2', str(codigo)).replace('$1', data)
                self.cursor.execute(query_substituida)            
                self.conexao.commit()   
                return True            
            return None
        except Exception as e:
            print(f"\nErro no update de data e processar na tabela logatualizacao: {e}\n({query_substituida})\n")
            return None
        
    