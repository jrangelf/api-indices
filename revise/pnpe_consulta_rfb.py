import requests
import datetime
from datetime import datetime
from bs4 import BeautifulSoup

class ReceitaFederal:
     
    @classmethod
    def consulta_selic_receita():
            url = 'https://sicalc.receita.economia.gov.br/sicalc/selic/consulta'    
            response = requests.get(url)
            # Verifique se a requisição foi bem-sucedida
            if response.status_code == 200:
                html = response.content
            else:
                print('Falha ao acessar a página:', response.status_code)
                return None        
            # Texto do <th> que você deseja encontrar (parte que existe no texto do <th>)
            th_text_part = 'Última Selic disponível'       
            soup = BeautifulSoup(html, 'html.parser')
            # Encontre o elemento <th> cujo texto é similar ao th_text_part 
            similar_th_elements = [th for th in soup.find_all('th') if th_text_part in th.get_text()]
            if similar_th_elements:
                for th_element in similar_th_elements:
                    # Obtenha o texto completo do <th>
                    th_full_text = th_element.get_text()
                    # Encontre o próximo elemento <td> associado ao <th>
                    td_element = th_element.find_next('td')            
                    if td_element:
                        td_content = td_element.get_text()
                        print("============================================ Receita Federal")
                        print('Texto completo do <th>:', th_full_text)
                        print('Conteúdo do <td> associado:', td_content)
                        print("============================================================")
                    else:
                        print('Não foi encontrado um <td> associado ao <th>:', th_full_text)
            else:
                print('Não foi encontrado nenhum <th> similar ao texto procurado:', th_text_part)
            texto = th_full_text
            # Encontrar a parte do texto que contém a data
            inicio = texto.find("(") + 1
            fim = texto.find(")")
            data_texto = texto[inicio:fim]

            # Converter a data_texto para um objeto de data
            data = datetime.strptime(data_texto, "%m/%Y").date()
            valor = float(td_content.replace(',','.'))        
            return data, valor
