import json
import requests

class ApiIndex():


    def consulta_por_mes_ano(self, indexador, mes, ano):
        url = f"http://api-indice:8001/{indexador}/{mes}/{ano}"
        try:
            response = requests.get(url)    
            if response.status_code == 200:
                item = json.loads(response.text)
                if 'valor' in item:
                    data, valor = item.get('data'), float(item.get('valor'))
                    return data, valor
                else:
                    return item
            else:
                print(f"Erro ao acessar a API. Código de status: {response.status_code}")
                return None
        except Exception as e:
            print(f"Erro na consulta por mes e ano na API: {e}")
            return None


    def consulta_por_periodo(self, indexador, mes_inicial, ano_inicial, mes_final, ano_final):
        url = f'http://api-indice:8001/{indexador}/periodo?mes_inicial={mes_inicial}&ano_inicial={ano_inicial}&mes_final={mes_final}&ano_final={ano_final}'
        try:
            response = requests.get(url)        
            if response.status_code == 200:
                data = json.loads(response.text)
                if 'valor' in data:
                    df = [{'data': item['data'], 'valor': float(item['valor'])} for item in data]
                    return df
                else:
                    return data
            else:
                print(f"Erro ao acessar a API. Código de status: {response.status_code}")
                return None
        except Exception as e:
            print(f"Erro na consulta por perido na API: {e}")
            return None

    
