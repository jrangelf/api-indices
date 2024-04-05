class SQLData:

    def __init__(self, conexao, queries_sql, datetools):
        self.conexao = conexao
        self.queries_sql = queries_sql
        self.datetools = datetools
    
    def buscar_nome_e_codigo_das_tabelas(self):
        conn = self.conexao()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(self.queries_sql.consulta_1)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows             
        return None
    
    def seleciona_ultima_data_das_tabelas(self,registros):
        lista = []
        conn = self.conexao()
        if conn is not None:
            cursor = conn.cursor()
            for registro in registros:
                consulta_substituida = self.queries_sql.consulta_2.replace('$', registro[0])
                cursor.execute(consulta_substituida)
                row = cursor.fetchone()
                lista.append((registro[0], registro[1], row[0]))            
            cursor.close()
            conn.close()
            return lista
        return None
    
    def atualizar_datas_logatualizacao(self,tupla):    
        tabs_atualizadas = []
        conn = self.conexao()
        if conn is not None:            
            cursor = conn.cursor()            
            for tabela, codigo, data in tupla:

                #print(f"tabela:{tabela} codigo:{codigo} data:{data}")
                #print("=============================================")
                #print("data_atualizacao (logatualizacao) atualizada ")
                
                # converter a data -> data.strftime("%Y-%m-%d")
                data_formatada = self.datetools.formatar_data_str_ymd(data) 
                try:
                    substituida = self.queries_sql.consulta_3.replace('$1', data_formatada).replace('$2', str(codigo))            
                    cursor.execute(substituida)
                    tabs_atualizadas.append((tabela, data_formatada))                
                    conn.commit()
                except Exception as e:                    
                    return f"Erro ao executar query para {tabela}\n{substituida}\nErro:{e}"                            
            return tabs_atualizadas                                        
        return None

