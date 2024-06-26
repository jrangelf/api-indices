import pandas as pd

class Juros:
    
    def __init__(self, datetools, tabelas, apiindex):        
        self.datetools = datetools        
        self.tabelas = tabelas
        self.apiindex = apiindex

    def zerar_processar(self, codigo, hoje, data):
        # print(f"data:{data}  dia_de_hoje:{hoje}")
        # print(f"veficar_data_atualizacao: {self.datetools.verificar_data_atualizacao(codigo, hoje, data)}")                   
        
        if not self.datetools.verificar_data_atualizacao(codigo, hoje, data):
            return self.tabelas.zerar_processar(codigo, str(data))
                        
    def atualizar_tabela_poupanca(self, indexador, tabela, codigo, data, proximo_mes, mes, ano, hoje):
        reg_selic = self.apiindex.consulta_por_mes_ano(indexador.lower(), mes, ano)
        if reg_selic:
            valor_selic = reg_selic[1]
            valor_selic_per = valor_selic/100        
            print (f"selic_copom: {valor_selic}  {indexador.lower()}")
            if valor_selic:                                      
                if valor_selic <= 8.5:                       
                    taxa_mensal = ((1+(0.7 * (valor_selic_per))) ** (1/12))-1
                else:
                    taxa_mensal = 0.005
                print(f"selic: {valor_selic_per}   taxa mensal: {taxa_mensal}")
                reg = self.tabelas.atualizar_tabela_poupanca(tabela, data, valor_selic_per, taxa_mensal)                
                if reg:
                    atualizada = self.tabelas.inserir_linha_tabela_poupanca(tabela,proximo_mes)
                    if atualizada:
                        self.zerar_processar(codigo, hoje, proximo_mes)                    
                        return atualizada
        return None
 
    
    def atualizar_tabela_selic(self, indexador, tabela, codigo, proximo_mes, 
                               mes, ano, hoje, ultimo_registro):
                
        print(f"indexador:{indexador}")
        print(f"codigo:{codigo}")
        
        selic_acumulada = float(ultimo_registro[3])
        reg_selic = self.apiindex.consulta_por_mes_ano(indexador.lower(), mes, ano)
        data_ultimo_registro = ultimo_registro[1]

        if reg_selic:
            selic = float(reg_selic[1])/100
            nova_selic_acumulada = round(selic + selic_acumulada,6)
            print(f"selic:{selic}")
            print(f"selic acumulada:{selic_acumulada}")
            print(f"nova selic acumulada: {nova_selic_acumulada}")
            
            atualizada = self.tabelas.atualizar_tabela_selic(tabela, data_ultimo_registro, selic)
            if atualizada:
                inserir_linha = self.tabelas.inserir_linha_tabela_selic(tabela, proximo_mes,
                                                                    nova_selic_acumulada)
                if inserir_linha:                     
                    tabela_pd = self.tabelas.carregar_tabela_selic(tabela)                       
                    
                    if tabela_pd:
                        
                        df = pd.DataFrame(tabela_pd, columns=['data','selic','selic_acumulada','selic_acumulada_mensal']) 
                        df.iloc[0,3] = nova_selic_acumulada
                        df[['selic','selic_acumulada', 'selic_acumulada_mensal']] = df[['selic','selic_acumulada', 'selic_acumulada_mensal']].astype(float)
                    
                        for i in range(1,df.shape[0]):
                            df.at[i, 'selic_acumulada'] = round(df.at[i-1, 'selic_acumulada'] + df.at[i-1, 'selic'],4)
                            df.at[i, 'selic_acumulada_mensal'] = round(df.at[i-1, 'selic_acumulada_mensal'] - df.at[i-1, 'selic'],4)
                        
                        print(f"Dataframe: \n{df}\n")
                        reg = self.tabelas.ajustar_selic_acumulada_mensal(tabela, df)
                        if reg:
                            self.zerar_processar(codigo, hoje, proximo_mes)                    
                            return reg

        return None
    

    def atualizar_tabela_juros(self, indexador, tabela, codigo, proximo_mes, 
                               mes, ano, hoje, ultimo_registro):                
        reg_poupanca = self.apiindex.consulta_por_mes_ano(indexador, mes, ano)
        if reg_poupanca:
            taxa_mensal = float(reg_poupanca['taxa_mensal'])
            juros_acumulados = float(ultimo_registro[3])
            novos_juros_acumulados = round(juros_acumulados + taxa_mensal,6)            
            atualizada = self.tabelas.inserir_linha_tabela_juros(tabela,proximo_mes,
                                                                 taxa_mensal,novos_juros_acumulados)
            if atualizada:                
                self.zerar_processar(codigo, hoje, proximo_mes)                    
                return atualizada
    
    

    def atualizar_juros(self):
        
        registros = self.tabelas.obter_tabelas_agendadas()
        if registros is None:
            return None
        
        tabelas_agendadas = [registro for registro in registros if 300 <= registro[2] < 400]        

        if len(tabelas_agendadas) == 0:
            return None
        
        hoje = self.datetools.dia_de_hoje()
        print(f'\nTabelas de juros para atualizar:')
        for tab in tabelas_agendadas:
            print (f"({tab[0]} : {tab[1]})")

        for tabela, indexador, codigo in tabelas_agendadas:
            print(f"\nTabela: {tabela}")
            ultimo_registro = self.tabelas.obter_ultimo_registro_da_tabela(tabela)
            data = ultimo_registro[1]
            mes, ano = ultimo_registro[1].month, ultimo_registro[1].year
            proximo_mes = self.datetools.incrementa_mes_obj(data)

            print(f"data ultimo registro: {data}  : {mes}/{ano}")
            print(f"mes subsequente: {proximo_mes}")
            
            # todas as tabelas de juros dependem da tabela de juros da poupanca. Assim, caso 
            # a tabela de juros da poupanca esteja mais atualizadas que as outras, as outras 
            # vao buscar os valores dos juros na tabela de juros da poupanca.

            if codigo == 300: 
               reg = self.atualizar_tabela_poupanca(indexador, tabela, codigo, data,
                                                    proximo_mes, mes, ano, hoje)               
            elif codigo == 312:  
                reg = self.atualizar_tabela_selic(indexador, tabela, codigo, proximo_mes,
                                                    mes, ano, hoje, ultimo_registro)                
            else:
                # o indice sera o indice de juros da poupanca
                indexador = 't300_juros_poupanca'
                reg = self.atualizar_tabela_juros(indexador, tabela, codigo, proximo_mes,
                                                  mes, ano, hoje, ultimo_registro)                
            
        return None
