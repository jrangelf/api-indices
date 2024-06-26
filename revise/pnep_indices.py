import pandas as pd


class Indices:
    
    def __init__(self, datetools, tabelas, apiindex):        
        self.datetools = datetools        
        self.tabelas = tabelas
        self.apiindex = apiindex
        
    def carregar_tabela(self, nome_tabela):
        registros = self.tabelas.carregar_tabela_pnep_indice(nome_tabela)
        if registros:
            return registros
        return None
    
    def atualizar_indices(self):
        obter_tabelas = self.tabelas.obter_tabelas_agendadas()
        
        if obter_tabelas is None:
            return None
                
        tabelas_agendadas = [tabela for tabela in obter_tabelas if 200 <= tabela[2] < 300]          
        
        if len(tabelas_agendadas) == 0:
            return None
        
        hoje = self.datetools.dia_de_hoje()        
        print(f'\nTabelas de indices PNEP para atualizar:')
        
        for i in tabelas_agendadas:
            print (f"{i[0]} indexador: {i[1]}")
                
        pd.set_option('display.float_format', '{:.8f}'.format)
        
        for tabela, indexador, codigo in tabelas_agendadas:
            print(f"\nTabela: {tabela}")

            ultimo_registro = self.tabelas.obter_ultimo_registro_da_tabela(tabela)
            if ultimo_registro:
                data, nome_index = ultimo_registro[1], ultimo_registro[2]
                mes, ano = ultimo_registro[1].month, ultimo_registro[1].year
                fator_vigente, indice_correcao = ultimo_registro[5], ultimo_registro[6]
                proximo_mes = self.datetools.incrementa_mes_obj(data)
                        
                print (f"data ultimo registro: {data}  {mes}/{ano}")
                print (f"fator_vigente: {fator_vigente}  indice_correcao: {indice_correcao}")
                print(f"mes subsequente: {proximo_mes}")

                valor_corrente = self.apiindex.consulta_por_mes_ano(indexador.lower(), mes, ano)
                
                if valor_corrente:
                    print(f"valor_corrente: {valor_corrente}")
                    valor = float(valor_corrente[1]) / 100
                    numero_indice = 1 + valor
                    novo_fator_vigente = float(fator_vigente) * numero_indice
                
                    print(f"indexador: {indexador.lower()}\nvalor: {valor}\nnumero_indice:{numero_indice}")
                    print(f"novo_fator_vigente: {novo_fator_vigente}")                       
                
                    tabela_pd = self.tabelas.carregar_tabela_pnep_indice(tabela)                       
                    df = pd.DataFrame(tabela_pd, columns=['data','indexador','variacao_mensal','numero_indice','fator_vigente','indice_correcao']) 
                            
                    # Alterar os valores da última linha
                    df.iloc[-1, df.columns.get_loc('variacao_mensal')] = valor
                    df.iloc[-1, df.columns.get_loc('numero_indice')] = numero_indice            
                    df['indice_correcao'] = round((novo_fator_vigente / df['fator_vigente'].astype(float)),8)
                    
                    print("DataFrame atualizado:")
                    print(df)
                    
                    reg = self.tabelas.atualizar_tabela_pnep_indice(tabela, df)
                    
                    if reg:
                        atualizada = self.tabelas.inserir_linha_tabela_indice_pnep(tabela,
                                                                        proximo_mes,
                                                                        nome_index,
                                                                        novo_fator_vigente)
                        if atualizada:
                            #print(f"proximo_mes: {proximo_mes}")
                            #print(f"data:{data}  dia_de_hoje:{hoje}")
                            #print(f"veficar_data_atualizacao: {self.datetools.verificar_data_atualizacao(codigo,hoje,proximo_mes)}")
                        
                            if not self.datetools.verificar_data_atualizacao(codigo, hoje, proximo_mes):
                                self.tabelas.zerar_processar(codigo, str(proximo_mes))
                                print (f"{atualizada}\n")                
                    
        return None
    