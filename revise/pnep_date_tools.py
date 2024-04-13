from datetime import datetime, timedelta

class DateTools:    
    
    def formatar_data_str_ymd(self,data):
        return data.strftime("%Y-%m-%d")

    def formatar_data_str_dmy(self, data):
        return data.strftime("%d/%m/%Y")

    @staticmethod
    def dia_de_hoje():
        return datetime.now()
    
    
    def formatar_data_inicio_mes(data):
        return data.strftime("01/%m/%Y")

    def verificar_data_atualizacao(self, codigo, data_atual, data_log):
        ''' 1. atualiza o campo processar para 1 caso a diferença de meses entre a data atual e a 
            data da ultima atualizacao de cada tabela de indexadores for maior ou igual a 2
            2. atualiza o campo processar para 1 caso a diferenca de meses entre a data atual e a 
            data da ultima atualizacao de cada tabela de indices pnep for maior ou igual a 1
            3. caso as datas estejam em anos diferentes o campo processar eh atualizado para 1
        '''
        if (data_atual.year > data_log.year):
            return True
        
        elif codigo < 200 and (data_atual.month - data_log.month >=2):
            #print(f"(1xx) mes atual - mes log = {data_atual.month - data_log.month}")
            return True
        
        elif codigo >= 200 and (data_atual.month - data_log.month <2):
            print(f"(2xx) mes atual - mes log = {data_atual.month - data_log.month}")
            return True
        
        return False


    def formatar_dmy_para_ymd(data_str):
        ''' converte a string 01/07/2023 em 2023-07-01 '''
        partes = data_str.split("/")
        nova_data = f"{partes[2]}-{partes[1]}-{partes[0]}"
        return nova_data

    def verificar_quinzena(data1):
        return data1.day == 15    

    def mesmo_mes(data1, data2):
        return data1.year == data2.year and data1.month == data2.month

    def mesmo_ano(data1, data2):
        return data1.year == data2.year

    def formato_ano_mes_dia(data_str):
        ''' converte a string 01/07/2023 em 2023-07-01 '''
        partes = data_str.split("/")
        nova_data = f"{partes[2]}-{partes[1]}-{partes[0]}"
        return nova_data

    def formatar_dataobj_para_string_dmy(data_obj):
        ''' converte a data 2023-07-01 00:00:00+0000 em 01/07/2023 '''    
        data_formatada = data_obj.strftime("%d/%m/%Y")
        return data_formatada

    def converter_data_para_str(data_obj):
        ''' converte a data 2023-07-01 00:00:00+0000 em 01/07/2023 '''    
        data_formatada = data_obj.strftime("%d/%m/%Y")
        return data_formatada

    def converter_data_para_str_slim(data_obj):
        data_formatada = data_obj.strftime("%Y-%m-%d")
        return data_formatada

    def converter_string_para_datetime(data_str):
        ''' converte a data 01/07/2023 para 2023-07-01 00:00:00+0000 '''
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        return data_obj

    def incrementa_mes(data):
        ''' converte 2023-07-01 00:00:00+0000 em 2023-08-01 00:00:00+0000'''    
        if data is not None:        
            ano = data.year + (data.month + 1) // 12
            mes = (data.month + 1) % 12
            if mes == 0:
                mes = 12       
            dia = min(data.day, (data.replace(month=mes, year=ano) - timedelta(days=1)).day)        
            data_incrementada = data.replace(year=ano, month=mes, day=1)        
            return data_incrementada
        
    def incrementa_mes_str(data_str):
        # Converter a string de data para um objeto datetime
        data = datetime.strptime(data_str, '%d/%m/%Y')
        # Incrementar o mês
        data_proximo_mes = data.replace(day=1) + timedelta(days=32)
        data_proximo_mes_formatado = data_proximo_mes.strftime('01/%m/%Y')
        return data_proximo_mes_formatado