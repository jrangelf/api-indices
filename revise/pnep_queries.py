class QueriesSQL:

    ''' seleciona todas as tabelas de indexadores e de indices pnep '''
    consulta_1 = "SELECT nome, codigo, indexador FROM descricao_tabelas \
        WHERE codigo < 300" 
    
    ''' seleciona a coluna data do último registro da tabela '''
    consulta_2 = "SELECT data FROM $ ORDER BY id DESC LIMIT 1" 
    
    ''' faz um update das datas de atualização da tabela logatualizacao'''
    consulta_3 = "UPDATE logatualizacao SET data_atualizacao='$1' WHERE codigo_tabela=$2"


    consulta_4 = "SELECT B.nome, A.data_atualizacao \
           FROM logatualizacao A \
           INNER JOIN indexadores B ON A.indexador = B.codigo \
           WHERE A.processar=1"
    
    ''' seleciona a codigo e data de atualização na tabela logatualizacao '''
    consulta_5 = "SELECT codigo_tabela, data_atualizacao FROM logatualizacao"

    
    
    ''' faz um update da coluna processar da tabela logatualizacao'''
    atualizacao_1 = "UPDATE logatualizacao SET processar=1 WHERE codigo_tabela=$"





    