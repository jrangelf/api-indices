# Backup e restauração do PostgreSQL

## 1. Objetivo

Este documento apresenta os procedimentos para geração, armazenamento e restauração dos backups do banco de dados `indices`, utilizado pelo projeto `api-indices`.

O procedimento permite recuperar o banco de dados em uma nova instalação do projeto ou em caso de perda ou corrupção dos dados existentes.

## 2. Configuração do ambiente

| Componente | Configuração |
|---|---|
| Projeto | api-indices |
| Container PostgreSQL | pgsqlapi |
| Imagem Docker | pgsqlapi:latest |
| Imagem base | postgres:15-trixie |
| Banco de dados | indices |
| Usuário PostgreSQL | postgres |
| Ferramenta de backup | pg_dump |
| Ferramenta de restauração | psql |
| Formato do backup | SQL |

## 3. Geração do backup

O backup lógico do banco de dados é realizado utilizando o utilitário `pg_dump` do PostgreSQL.

Exemplo de comando executado na máquina host:

```bash
docker exec pgsqlapi pg_dump -U postgres indices \
    > "indices_$(date '+%d-%m-%Y_%H%M%S').sql"
```

Os arquivos gerados seguem o padrão:

```text
indices_DD-MM-AAAA_HHMMSS.sql
```

O arquivo contém as instruções SQL necessárias para reconstruir as tabelas, registros, índices, sequências e demais objetos contemplados pelo backup.

## 4. Localização dos backups

Os arquivos de backup são armazenados externamente no Google Drive e não fazem parte do repositório GitHub.

Para obter o arquivo de backup mais atualizado, consultar as instruções disponíveis no [README principal do projeto](../README.md).

Após realizar o download, colocar o arquivo no diretório:

```text
api-indices/pgsqlapi/backup/
```

## 5. Restauração do banco de dados

### 5.1. Acessar o diretório do projeto

```bash
cd ~/dev/api-indices
```

Ajustar o caminho caso o projeto tenha sido instalado em outro diretório.

### 5.2. Verificar se o container está em execução

```bash
docker ps --filter name=pgsqlapi
```

O container `pgsqlapi` deverá estar em execução, apresentando o status `Up`.

### 5.3. Verificar o arquivo de backup

```bash
ls -lh pgsqlapi/backup/
```

Confirmar a existência do arquivo SQL, seu tamanho e sua data de geração.

### 5.4. Verificar a existência do banco de dados

```bash
docker exec pgsqlapi psql -U postgres -d postgres -c "\l"
```

Esse comando apresenta os bancos de dados existentes no PostgreSQL.

### 5.5. Preparar o banco de dados

A restauração deverá ser realizada preferencialmente em um banco de dados vazio, evitando conflitos com objetos e registros existentes.

**ATENÇÃO:** caso o banco `indices` já exista e contenha dados, realizar um backup de segurança antes de prosseguir. Interromper também as aplicações e rotinas que utilizam o banco.

Se for necessário excluir o banco existente:

```bash
docker exec pgsqlapi dropdb -U postgres --if-exists indices
```

Esse comando exclui permanentemente o banco de dados `indices`.

Criar um novo banco de dados vazio:

```bash
docker exec pgsqlapi createdb -U postgres -T template0 indices
```

O parâmetro `-T template0` determina a utilização de um modelo limpo para a criação do banco.

Caso o banco já exista e esteja comprovadamente vazio, não é necessário excluí-lo e recriá-lo.

### 5.6. Executar a restauração

Executar o seguinte comando:

```bash
docker exec -i pgsqlapi psql -U postgres -d indices \
    -v ON_ERROR_STOP=1 --single-transaction \
    < pgsqlapi/backup/NOME_DO_ARQUIVO.sql
```

Substituir `NOME_DO_ARQUIVO.sql` pelo nome do arquivo de backup baixado.

Exemplo:

```bash
docker exec -i pgsqlapi psql -U postgres -d indices \
    -v ON_ERROR_STOP=1 --single-transaction \
    < pgsqlapi/backup/indices_28-11-2026_130000.sql
```

Descrição dos argumentos:

| Argumento | Finalidade |
|---|---|
| docker exec | Executa um comando dentro do container. |
| -i | Mantém a entrada padrão aberta. |
| pgsqlapi | Nome do container PostgreSQL. |
| psql | Cliente de linha de comando do PostgreSQL. |
| -U postgres | Usuário utilizado na conexão. |
| -d indices | Banco de dados de destino. |
| -v ON_ERROR_STOP=1 | Interrompe a execução caso ocorra um erro SQL. |
| --single-transaction | Executa a restauração em uma única transação. |
| < | Redireciona o conteúdo do arquivo SQL para o comando. |

Não é necessário copiar o arquivo SQL para dentro do container.

### 5.7. Verificar o resultado da restauração

Imediatamente após a execução do comando anterior, executar:

```bash
echo $?
```

O código de saída `0` indica que o comando foi executado com sucesso. Um valor diferente de zero indica a ocorrência de erro.

## 6. Validação do banco de dados

### 6.1. Verificar as tabelas restauradas

```bash
docker exec pgsqlapi psql -U postgres -d indices -c "\dt"
```

### 6.2. Verificar a quantidade de registros

```bash
docker exec pgsqlapi psql -U postgres -d indices \
    -c "SELECT COUNT(*) FROM selic;"
```

Também é possível verificar outras tabelas importantes:

```bash
docker exec pgsqlapi psql -U postgres -d indices \
    -c "SELECT COUNT(*) FROM ipca;"
```

```bash
docker exec pgsqlapi psql -U postgres -d indices \
    -c "SELECT COUNT(*) FROM inpc;"
```

```bash
docker exec pgsqlapi psql -U postgres -d indices \
    -c "SELECT COUNT(*) FROM indexadores;"
```

Sempre que possível, comparar as quantidades de registros com as existentes no banco de origem na data do backup.

### 6.3. Verificar a versão de collation

```bash
docker exec pgsqlapi psql -U postgres -d indices -c "
SELECT
    datname,
    datcollate,
    datctype,
    datcollversion AS versao_registrada,
    pg_database_collation_actual_version(oid) AS versao_atual
FROM pg_database
WHERE datname = 'indices';
"
```

A versão registrada e a versão atual da collation deverão ser compatíveis.

Caso seja identificada alguma divergência, consultar o documento [README_COLLATION.md](README_COLLATION.md).

### 6.4. Atualizar as estatísticas do banco

```bash
docker exec pgsqlapi psql -U postgres -d indices -c "ANALYZE;"
