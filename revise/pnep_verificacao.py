class VerificacaoTabelas:

    def __init__(self, sqldata):
        self.sqldata = sqldata
    
    def obter_datas_atualizacao_tabelas(self):
        ''' retorna o nome, o codigo e a data de atualizacao de cada tabela
            de indexadores do banco central e cada tabela de indice do Pnep'''
               
        # busca o nome e o codigo de todas as tabelas
        registros = self.sqldata.buscar_nome_e_codigo_das_tabelas()
        # seleciona a data que esta no ultimo registro
        tabela_e_data_atualizacao = self.sqldata.seleciona_ultima_data_das_tabelas(registros)        
        if tabela_e_data_atualizacao:
            return tabela_e_data_atualizacao                
        return None
    
    def atualizar_logatualizacao(self, tupla):        
        atualizadas = self.sqldata.atualizar_datas_logatualizacao(tupla)
        if atualizadas:
            return atualizadas               
        return None
    
    
    def marcar_tabelas_para_atualizacao(self):
        pass


