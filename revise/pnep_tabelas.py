#from pnep_sqldata import SQLData

class Tabelas:

    def __init__(self, sqldata):
        self.sqldata = sqldata
    
    def obter_datas_atualizacao_tabelas(self):
        ''' retorna o nome, o codigo e a data de atualizacao de cada tabela
            de indexadores do banco central e cada tabela de indice do Pnep'''
               
        # busca o nome e o codigo de todas as tabelas
        registros = self.sqldata.buscar_nome_e_codigo_das_tabelas()
        #print(f'registros:\n{registros}')

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
    
    def marcar_tabelas_para_atualizacao(self, _data_atual):
        tabelas_para_processar = self.sqldata.indicar_tabelas_para_atualizacao(_data_atual)
        if tabelas_para_processar:
            return tabelas_para_processar
        return None       

    def buscar_codigo_bcb_indexadores(self):
        pass


