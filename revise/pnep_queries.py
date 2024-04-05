class QueriesSQL:

    ''' seleciona todas as tabelas de indexadores e de indices pnep '''
    consulta_1 = "SELECT nome, codigo FROM descricao_tabelas \
        WHERE codigo < 300" 
    
    ''' seleciona a coluna data do último registro da tabela '''
    consulta_2 = "SELECT data FROM $ ORDER BY id DESC LIMIT 1" 
    
    ''' faz um update das datas de atualização da tabela logatualizacao'''
    consulta_3 = "UPDATE logatualizacao SET data_atualizacao='$1' WHERE codigo_tabela=$2"




    