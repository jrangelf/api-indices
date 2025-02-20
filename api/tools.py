def ajusta_nome_tabela(tabela_id: int):
    code = str(tabela_id)
    pref = 'T0'+ code  if len(code) < 2 else 'T' + code  
    return pref + 'tabeladcp' 


def converter_var_per_mensal_para_porcentagem(tabela):
    pass