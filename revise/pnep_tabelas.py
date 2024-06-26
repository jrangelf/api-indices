

class Tabelas: 

    def __init__(self, sqldata):
        self.sqldata = sqldata
    
    def obter_datas_atualizacao_tabelas(self):        
        registros = self.sqldata.buscar_nome_e_codigo_das_tabelas()
        tabela_e_data_atualizacao = self.sqldata.seleciona_ultima_data_das_tabelas(registros)
        if tabela_e_data_atualizacao:            
            return tabela_e_data_atualizacao                
        return None
    
    def atualizar_datas_logatualizacao(self, tupla):        
        atualizadas = self.sqldata.atualizar_datas_logatualizacao(tupla)
        if atualizadas:
            return atualizadas               
        return None    
    
    def marcar_tabelas_para_atualizacao(self, _data_atual):
        tabelas_para_processar = self.sqldata.marcar_tabelas_para_atualizacao(_data_atual)
        if tabelas_para_processar:
            return tabelas_para_processar
        return None
        
    def buscar_codigo_bcb_indexadores(self, registros):
        codigos_bcb = self.sqldata.buscar_codigo_bcb_indexadores(registros)
        if codigos_bcb:
            return codigos_bcb
        return None

    def inserir_indice_bcb(self, dt_formatada, valor, codigotab):
        indice_inserido = self.sqldata.inserir_indice_bcb(dt_formatada, valor, codigotab)
        if indice_inserido:
            return indice_inserido
        return None
    
    def zerar_processar(self, codigo, data):
        situacao = self.sqldata.zerar_processar(codigo, data)
        if situacao:
            return True
        return None
    
    def carregar_tabela_pnep_indice(self, nome_tabela):
        tabela = self.sqldata.carregar_tabela_pnep_indice(nome_tabela)
        if tabela:
            return tabela
        return None
    
    def carregar_tabela_selic(self, nome_tabela):
        tabela = self.sqldata.carregar_tabela_selic(nome_tabela)
        if tabela:
            return tabela
        return None
    
    def obter_tabelas_agendadas(self):
        tabelas = self.sqldata.obter_tabelas_agendadas()
        if tabelas:
            return tabelas
        return None
    
    def obter_ultimo_registro_da_tabela(self, nome_tabela):
        registro = self.sqldata.obter_ultimo_registro_da_tabela(nome_tabela)
        if registro:
            return registro
        return None
    
    def atualizar_tabela_pnep_indice(self, nome_tabela, df):
        registro = self.sqldata.atualizar_tabela_pnep_indice (nome_tabela, df)
        if registro:
            return registro
        return None
    
    def atualizar_tabela_poupanca(self, nome_tabela, data, meta_selic, taxa_mensal):
        registro = self.sqldata.atualizar_tabela_poupanca(nome_tabela, data, meta_selic, taxa_mensal)
        if registro:
            return registro
        return None
    
    def atualizar_tabela_selic(self, nome_tabela, data, selic):
        registro = self.sqldata.atualizar_tabela_selic(nome_tabela, data, selic)
        if registro:
            return registro
        return None
    
    def ajustar_selic_acumulada_mensal(self,nome_tabela, df):
        registro = self.sqldata.ajustar_selic_acumulada_mensal(nome_tabela, df)
        if registro:
            return registro
        return None
    
    
    def inserir_linha_tabela_indice_pnep(self,
                                         nome_tabela, 
                                         data, 
                                         indexador, 
                                         fator_vigente):
        
        linha = self.sqldata.inserir_linha_tabela_indice_pnep(nome_tabela,
                                                              data,
                                                              indexador,
                                                              fator_vigente)
        if linha:
            return linha
        return None
        
    def inserir_linha_tabela_poupanca(self,nome_tabela,proximo_mes):               
        linha = self.sqldata.inserir_linha_tabela_poupanca(nome_tabela, proximo_mes)
        if linha:
            return linha
        return None

    def inserir_linha_tabela_juros(self, nome_tabela, proximo_mes, taxa_mensal, novos_juros_acumulados):
        linha = self.sqldata.inserir_linha_tabela_juros(nome_tabela,
                                                        proximo_mes,
                                                        taxa_mensal,
                                                        novos_juros_acumulados)
        if linha:
            return linha
        return None
                
    def inserir_linha_tabela_selic(self, nome_tabela, proximo_mes, nova_selic_acumulada):
        linha = self.sqldata.inserir_linha_tabela_selic(nome_tabela,
                                                        proximo_mes,
                                                        nova_selic_acumulada)
        if linha:
            return linha
        return None
    
    