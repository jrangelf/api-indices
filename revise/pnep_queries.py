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

    ''' seleciona os codigos dos indexadores do banco central'''
    consulta_6 = "SELECT descricao FROM indexadores WHERE codigo = $"

    

     
    consulta_7 = "SELECT indexadores.nome, descricao_tabelas.nome \
           FROM descricao_tabelas \
           JOIN indexadores ON descricao_tabelas.indexador = indexadores.codigo \
           JOIN logatualizacao ON descricao_tabelas.indexador = logatualizacao.indexador \
           WHERE logatualizacao.processar = 1" 
    
    
    ''' faz um update da coluna processar da tabela logatualizacao para 1'''
    atualizacao_1 = "UPDATE logatualizacao SET processar=1 WHERE codigo_tabela=$"

    ''' faz um update da coluna processar da tabela logatualizacao para 0'''
    atualizacao_2 = "UPDATE logatualizacao SET processar=0, data_atualizacao='$1' WHERE codigo_tabela=$2"



    ''' faz um insert de data e valor na tabela de indexador '''
    insercao_1 = "INSERT INTO $1(data, valor) VALUES ('$2', $3)"



    