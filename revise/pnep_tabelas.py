#from pnep_sqldata import SQLData

class Tabelas: 

    def __init__(self, sqldata):
        self.sqldata = sqldata
    
    def obter_datas_atualizacao_tabelas(self):        
        # busca o nome e o codigo de todas as tabelas
        registros = self.sqldata.buscar_nome_e_codigo_das_tabelas()        
        # seleciona a data que esta no ultimo registro
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