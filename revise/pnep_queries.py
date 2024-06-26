class QueriesSQL:

    ''' seleciona todas as tabelas de indexadores e de indices pnep '''
    consulta_1 = "SELECT nome, codigo, indexador FROM descricao_tabelas \
           WHERE codigo < 400" 
    
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

    consulta_8 = "SELECT data, indexador, variacao_mensal, numero_indice, \
           fator_vigente, indice_correcao FROM $ ORDER BY data"

    consulta_9 = "SELECT dt.nome AS nome_descricao_tabela, i.nome AS nome_indexador, la.codigo_tabela AS codigo \
           FROM logatualizacao AS la \
           JOIN descricao_tabelas AS dt ON la.codigo_tabela = dt.codigo \
           JOIN indexadores AS i ON la.indexador = i.codigo \
           WHERE la.processar = 1 AND la.codigo_tabela >= 200 \
           AND la.codigo_tabela < 400 \
           ORDER BY nome_descricao_tabela "

    consulta_10 = "SELECT * FROM $ ORDER BY id DESC LIMIT 1"

    consulta_11 = "SELECT data, selic, selic_acumulada, selic_acumulada_mensal FROM $ ORDER BY data"   
    
    ''' faz um update da coluna processar da tabela logatualizacao para 1'''
    atualizacao_1 = "UPDATE logatualizacao SET processar=1 WHERE codigo_tabela=$"

    ''' faz um update da coluna processar da tabela logatualizacao para 0'''
    atualizacao_2 = "UPDATE logatualizacao SET processar=0, data_atualizacao='$1' WHERE codigo_tabela=$2"

    ''' atualiza a tabela de indice com os novos valores mensais '''   
    atualizacao_3 = "UPDATE $1 SET variacao_mensal = $2, numero_indice = $3, fator_vigente = $4, indice_correcao = $5 WHERE data = '$6' "

    ''' atualiza a tabela poupanca '''   
    atualizacao_4 = "UPDATE $1 SET meta_selic_copom = $2, taxa_mensal = $3 WHERE data = '$4' "
   
    ''' atualiza a tabela selic '''   
    atualizacao_5 = "UPDATE $1 SET selic = $2 WHERE data = '$3' "
   
    ''' atualiza a tabela selic com os novos valores acumulados '''   
    atualizacao_6 = "UPDATE $1 SET selic_acumulada = $2, selic_acumulada_mensal = $3 WHERE data = '$4'"



    ''' faz um insert de data e valor na tabela de indexador '''
    insercao_1 = "INSERT INTO $1(data, valor) VALUES ('$2', $3)"

    ''' insere ultima linha na tabela de indice pnep '''
    insercao_2 = "INSERT INTO $1(data, indexador, numero_indice, fator_vigente, indice_correcao) \
               VALUES ('$2', '$3', $4, $5, $6)"   
    
    insercao_3 = "INSERT INTO $1(data) VALUES ('$2')"
    
    ''' insere nova linha na tabela de juros'''   
    insercao_4 = "INSERT INTO $1(data, juros_mensal, juros_acumulados) VALUES ('$2', $3, $4)"

    ''' insere nova linha na tabela selic'''   
    insercao_5 = "INSERT INTO $1(data, selic_acumulada) VALUES ('$2', $3)"