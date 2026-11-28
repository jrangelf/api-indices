
# Manutenção de Collation do PostgreSQL

## Projeto api-indices

---

## 1. Objetivo

Este documento apresenta os procedimentos para identificar, diagnosticar
e corrigir divergências de versões de collation do PostgreSQL executado
em containers Docker.

O script responsável pela manutenção é:

    pgsqlapi/corrigir_collation.sh

O procedimento contempla os seguintes bancos de dados:

- postgres
- template1
- indices

Também é possível informar outro banco de dados como argumento.

O banco template0 é protegido contra alterações realizadas pelo script.

---

## 2. O que é Collation?

Collation é um conjunto de regras utilizado pelo PostgreSQL para
comparação e ordenação de caracteres e textos.

Essas regras podem influenciar operações como:

- Ordenação de registros com ORDER BY.
- Comparação de strings.
- Criação e utilização de índices textuais.
- Restrições de unicidade.
- Ordenação de caracteres acentuados.
- Particionamento baseado em valores textuais.

O PostgreSQL pode utilizar bibliotecas do sistema operacional para
implementar essas regras.

Entre essas bibliotecas estão:

- GLIBC: GNU C Library.
- ICU: International Components for Unicode.

Quando essas bibliotecas são atualizadas, suas regras de comparação
e ordenação podem sofrer alterações.

---

## 3. Divergência de versões de Collation

O PostgreSQL armazena informações sobre as versões das collations.

Quando a versão registrada no banco é diferente da versão fornecida
pelo ambiente atual, pode ser apresentada uma mensagem semelhante a:

    WARNING: database "indices" has a collation version mismatch

    DETAIL: The database was created using collation version 2.36,
    but the operating system provides version 2.41.

    HINT: Rebuild all objects in this database that use the default
    collation and run ALTER DATABASE indices REFRESH COLLATION VERSION.

Essa divergência pode ocorrer em situações como:

- Atualização do sistema operacional.
- Atualização da biblioteca GLIBC.
- Atualização da biblioteca ICU.
- Alteração da imagem Docker do PostgreSQL.
- Migração de dados físicos entre ambientes diferentes.
- Reutilização de volumes criados em ambientes antigos.
- Restauração de backups físicos em ambientes diferentes.

A divergência não significa necessariamente que os dados estejam
corrompidos.

Entretanto, objetos que dependem das regras antigas de ordenação
podem precisar ser reconstruídos.

A simples atualização da versão registrada não garante a integridade
dos objetos dependentes.

---

## 4. Imagem Docker utilizada

O Dockerfile do PostgreSQL utiliza:

```dockerfile
FROM postgres:15-trixie
```

Essa configuração estabelece:

- PostgreSQL da série 15.
- Debian 13, denominado Trixie.
- Possibilidade de receber novas versões menores do PostgreSQL 15.

Anteriormente, o Dockerfile utilizava:

```dockerfile
FROM postgres:15.3
```

A utilização da tag 15-trixie permite acompanhar atualizações da
série 15 sem precisar alterar o Dockerfile a cada nova versão menor.

Entretanto, essa tag não fixa uma versão exata do PostgreSQL nem
das bibliotecas do sistema operacional.

Portanto, futuras atualizações ainda poderão provocar divergências
de collation.

Para obter uma versão mais recente da imagem base durante o build,
utilize, após os backups e o planejamento da manutenção:

```bash
docker compose build --pull
```

O argumento --pull solicita a atualização das imagens base utilizadas
durante o processo de construção.

O build não atualiza automaticamente um container que já está em
execução.

---

## 5. Estrutura do projeto

```text
api-indices/
├── pgsqlapi/
│   ├── dockerfile.pgsqlapi
│   ├── executar_tail_docker
│   ├── corrigir_collation.sh
│   ├── README_COLLATION.md
│   ├── db/
│   └── backup/
└── .gitignore
```

### Diretório db

Armazena os arquivos físicos do PostgreSQL.

### Diretório backup

Armazena os backups do PostgreSQL.

Esses dois diretórios não devem ser versionados no GitHub.

O arquivo .gitignore deve conter:

```gitignore
/pgsqlapi/db/
/pgsqlapi/backup/
```

Os backups devem ser mantidos também em um local independente
do servidor que executa o PostgreSQL.

---

## 6. Identificação do ambiente

### 6.1. Verificar os containers

```bash
docker ps
```

Apresenta os containers em execução.

### 6.2. Verificar a versão do PostgreSQL

```bash
docker exec pgsqlapi postgres --version
```

Exemplo de resultado:

    postgres (PostgreSQL) 15.20

### 6.3. Verificar o sistema operacional

```bash
docker exec pgsqlapi cat /etc/os-release
```

Apresenta informações sobre o sistema operacional utilizado
pelo container.

### 6.4. Verificar a versão da GLIBC

```bash
docker exec pgsqlapi getconf GNU_LIBC_VERSION
```

Exemplo de resultado:

    glibc 2.41

### 6.5. Verificar a imagem utilizada pelo container

```bash
docker inspect pgsqlapi --format '{{.Config.Image}}'
```

### 6.6. Verificar o diretório de dados

```bash
docker exec pgsqlapi printenv PGDATA
```

No ambiente utilizado durante os testes:

    /var/lib/postgresql/data/pgdata

### 6.7. Verificar os volumes e diretórios montados

```bash
docker inspect pgsqlapi --format '{{json .Mounts}}'
```

Esse comando permite identificar os diretórios do servidor
associados aos diretórios internos do container.

---

## 7. Pré-requisitos para manutenção

Antes de executar qualquer procedimento de correção:

- [ ] Verificar se o PostgreSQL está em execução.
- [ ] Identificar a versão do PostgreSQL.
- [ ] Identificar a versão do sistema operacional.
- [ ] Identificar a versão da GLIBC.
- [ ] Realizar um backup lógico atualizado.
- [ ] Realizar um backup físico, quando aplicável.
- [ ] Verificar a integridade dos backups.
- [ ] Conhecer o procedimento de restauração.
- [ ] Manter uma cópia dos backups fora do servidor.
- [ ] Interromper as aplicações que utilizam o banco.
- [ ] Suspender tarefas automatizadas que acessam o banco.
- [ ] Reservar uma janela de manutenção.
- [ ] Analisar os objetos dependentes das collations.
- [ ] Garantir espaço em disco suficiente para reconstrução dos índices.

O PostgreSQL deve permanecer em execução durante a utilização
do script.

A interrupção das aplicações não significa interromper o
container do PostgreSQL.

---

## 8. Backup lógico

O backup lógico contém comandos SQL necessários para reconstruir
os bancos de dados e seus objetos.

Para realizar um backup completo do cluster PostgreSQL:

```bash
docker exec pgsqlapi sh -c '
    umask 077
    pg_dumpall -U "${POSTGRES_USER:-postgres}" \
        > /db/backup/backup_completo_$(date +%Y-%m-%d_%H%M%S).sql
'
```

### Explicação dos comandos

- docker exec: executa um comando dentro do container.
- sh -c: executa os comandos por meio de um interpretador shell.
- umask 077: restringe as permissões dos novos arquivos.
- pg_dumpall: gera um backup lógico dos bancos e objetos globais.
- -U: identifica o usuário do PostgreSQL.
- POSTGRES_USER: variável de ambiente que identifica o usuário.
- :-postgres: utiliza postgres caso a variável esteja vazia ou ausente.
- >: redireciona a saída para um arquivo.
- date: acrescenta a data e a hora ao nome do arquivo.

Exemplo de arquivo gerado:

    backup_completo_2026-11-28_150238.sql

O backup poderá conter informações sensíveis, incluindo hashes
de senhas de usuários do PostgreSQL.

Não disponibilize esses arquivos publicamente.

---

## 9. Backup físico

O backup físico contém uma cópia dos arquivos utilizados
internamente pelo PostgreSQL.

Para gerar um backup físico:

```bash
docker exec pgsqlapi sh -c '
    umask 077
    pg_basebackup \
        -U "${POSTGRES_USER:-postgres}" \
        -D /db/backup/fisico_$(date +%Y-%m-%d_%H%M%S) \
        -Ft \
        -z \
        -X stream \
        -P
'
```

O usuário utilizado deve possuir permissões adequadas para
realizar o backup físico.

### Explicação dos argumentos

| Argumento | Finalidade |
|-----------|------------|
| -U | Usuário do PostgreSQL |
| -D | Diretório de destino |
| -Ft | Formato TAR |
| -z | Compactação gzip |
| -X stream | Transmissão dos arquivos WAL durante o backup |
| -P | Exibição do progresso |

Exemplo de estrutura gerada:

```text
fisico_2026-11-28_150053/
├── backup_manifest
├── base.tar.gz
└── pg_wal.tar.gz
```

O backup físico deve ser restaurado em um ambiente compatível
com a versão principal do PostgreSQL e com as características
do ambiente original.

Diferentemente do backup lógico, ele preserva os arquivos físicos,
os índices e as versões de collation registradas no cluster.

---

## 10. Verificação dos backups

### 10.1. Listar os arquivos

```bash
docker exec pgsqlapi ls -lht /db/backup
```

Argumentos:

- -l: apresenta informações detalhadas.
- -h: apresenta tamanhos em formato legível.
- -t: ordena os arquivos pela data de modificação.

### 10.2. Verificar o final do backup lógico

```bash
docker exec pgsqlapi tail -n 15 \
    /db/backup/backup_completo_2026-11-28_150238.sql
```

Resultado esperado:

    PostgreSQL database cluster dump complete

Essa mensagem é um indicador de conclusão do backup, mas não
garante isoladamente sua integridade.

A verificação mais importante consiste em realizar uma
restauração de teste.

### 10.3. Verificar os arquivos compactados do backup físico

```bash
docker exec pgsqlapi gzip -tv \
    /db/backup/fisico_2026-11-28_150053/base.tar.gz \
    /db/backup/fisico_2026-11-28_150053/pg_wal.tar.gz
```

Argumentos:

- -t: testa a integridade do arquivo compactado.
- -v: apresenta informações detalhadas.

### 10.4. Extrair o backup físico para validação

```bash
docker exec pgsqlapi sh -c '
    set -e
    umask 077

    ORIGEM=/db/backup/fisico_2026-11-28_150053

    DESTINO=$(mktemp -d /db/backup/validacao_fisico_XXXXXX)

    tar -xzf "$ORIGEM/base.tar.gz" -C "$DESTINO"

    mkdir -p "$DESTINO/pg_wal"

    tar -xzf "$ORIGEM/pg_wal.tar.gz" \
        -C "$DESTINO/pg_wal"

    cp "$ORIGEM/backup_manifest" "$DESTINO/"

    echo "Backup extraído em: $DESTINO"
'
```

Esse exemplo considera um cluster sem tablespaces adicionais.

### 10.5. Validar com pg_verifybackup

Utilize o diretório apresentado pelo comando anterior.

Exemplo:

```bash
docker exec pgsqlapi pg_verifybackup \
    /db/backup/validacao_fisico_LAJsGf
```

Resultado esperado:

    backup successfully verified

O pg_verifybackup verifica o backup físico utilizando o manifesto
gerado pelo PostgreSQL.

Essa verificação não substitui completamente uma restauração
de teste.

Os nomes dos arquivos e diretórios apresentados nesta seção
correspondem aos backups utilizados durante os testes e devem
ser adaptados em futuras execuções.

---

## 11. Script de manutenção

### 11.1. Localização

    pgsqlapi/corrigir_collation.sh

### 11.2. Verificar a sintaxe Bash

```bash
bash -n pgsqlapi/corrigir_collation.sh
```

O argumento -n verifica a sintaxe sem executar o script.

Caso não existam erros, normalmente não será apresentada
nenhuma mensagem.

### 11.3. Executar com os argumentos padrão

A partir da raiz do projeto:

```bash
bash pgsqlapi/corrigir_collation.sh
```

Valores padrão:

| Argumento | Valor |
|-----------|-------|
| Container | pgsqlapi |
| Banco de dados | indices |

### 11.4. Informar explicitamente os argumentos

```bash
bash pgsqlapi/corrigir_collation.sh pgsqlapi indices
```

### 11.5. Executar em um ambiente de testes

```bash
bash pgsqlapi/corrigir_collation.sh \
    pgsqlapi-teste-fisico indices
```

### 11.6. Executar para outro banco de dados

```bash
bash pgsqlapi/corrigir_collation.sh \
    pgsqlapi-teste-fisico teste_collation
```

### 11.7. Argumentos

| Posição | Descrição | Valor padrão |
|---------|-----------|--------------|
| 1 | Nome do container | pgsqlapi |
| 2 | Nome do banco de dados | indices |

O script também analisa os bancos postgres e template1.

Caso postgres ou template1 seja informado como segundo argumento,
o script evita processar o mesmo banco duas vezes.

---

## 12. Funcionamento do script

O script realiza as seguintes operações:

1. Verifica se o banco informado é template0.
2. Define a lista de bancos sem duplicidades.
3. Verifica a disponibilidade do Docker.
4. Verifica se o container está em execução.
5. Verifica se o PostgreSQL aceita conexões.
6. Valida a existência do banco informado.
7. Identifica as versões do ambiente.
8. Consulta as versões de collation dos bancos.
9. Identifica divergências da collation padrão.
10. Diagnostica divergências das collations específicas.
11. Identifica objetos e índices dependentes.
12. Solicita autorização para manutenção.
13. Reconstrói índices dos bancos com divergência padrão.
14. Solicita autorização para atualizar a collation padrão.
15. Atualiza as versões registradas da collation padrão.
16. Apresenta exemplos dos comandos de atualização específicos.
17. Verifica dependências adicionais.
18. Solicita autorização para atualizar collations específicas.
19. Realiza uma verificação automática de dependências.
20. Atualiza as collations específicas quando permitido.

As etapas de reconstrução e atualização da collation padrão
são executadas somente quando existem divergências identificadas.

---

## 13. Correção da Collation padrão

Quando uma divergência da collation padrão é identificada,
o script utiliza comandos equivalentes aos seguintes:

### 13.1. Reconstrução dos índices

```sql
REINDEX DATABASE indices;
```

Esse comando reconstrói os índices abrangidos pela operação
no banco de dados informado.

O REINDEX DATABASE não reconstrói automaticamente todos os tipos
de objetos dependentes e não inclui os índices dos catálogos
de sistema.

Outros objetos afetados devem ser analisados separadamente.

### 13.2. Atualização da versão registrada

```sql
ALTER DATABASE indices REFRESH COLLATION VERSION;
```

Esse comando atualiza a versão de collation registrada
nos metadados do banco.

IMPORTANTE:

O comando REFRESH COLLATION VERSION não reconstrói índices
nem verifica automaticamente se todos os objetos dependentes
foram corrigidos.

A atualização somente deve ser autorizada depois da análise
e reconstrução dos objetos afetados.

---

## 14. Correção das Collations específicas

Além da collation padrão de cada banco, o PostgreSQL possui
collations específicas registradas no catálogo pg_collation.

Exemplo de atualização:

```sql
ALTER COLLATION pg_catalog."af-NA-x-icu"
REFRESH VERSION;
```

O script gera dinamicamente os comandos necessários.

A geração utiliza a função format do PostgreSQL:

```sql
SELECT format(
    'ALTER COLLATION %I.%I REFRESH VERSION;',
    n.nspname,
    c.collname
)
FROM pg_collation c
JOIN pg_namespace n
    ON n.oid = c.collnamespace
WHERE c.collversion IS NOT NULL
    AND pg_collation_actual_version(c.oid) IS NOT NULL
    AND c.collversion <>
        pg_collation_actual_version(c.oid);
```

O argumento %I permite tratar corretamente os identificadores
SQL, incluindo nomes que precisam de aspas.

Os comandos são executados utilizando:

    \gexec

Esse recurso do psql executa os comandos SQL produzidos
pela consulta anterior.

As atualizações das collations específicas são executadas
dentro de uma transação por banco de dados.

```sql
BEGIN;

-- Comandos de atualização.

COMMIT;
```

Se ocorrer um erro antes do COMMIT, as alterações daquela
transação não serão confirmadas.

Entretanto, alterações já confirmadas em outros bancos
não serão automaticamente desfeitas.

---

## 15. Proteções implementadas

### 15.1. Tratamento de erros Bash

```bash
set -euo pipefail
```

| Opção | Finalidade |
|-------|------------|
| -e | Interromper a execução diante de determinados erros |
| -u | Detectar utilização de variáveis não definidas |
| pipefail | Detectar falhas em pipelines |

### 15.2. Tratamento de erros SQL

```bash
-v ON_ERROR_STOP=1
```

Determina que o psql interrompa a execução quando ocorrer
um erro SQL.

### 15.3. Ignorar configurações pessoais do psql

```bash
psql -X
```

Impede o carregamento dos arquivos de configuração de
inicialização do psql.

### 15.4. Proteção do template0

O script não permite que template0 seja informado como
banco de dados para manutenção.

O template0 é um modelo original do PostgreSQL e normalmente
não permite conexões.

Uma eventual manutenção desse banco deve ser realizada por
meio de um procedimento administrativo específico.

### 15.5. Verificação de dependências

O script consulta os seguintes catálogos:

| Catálogo | Finalidade |
|----------|------------|
| pg_database | Informações dos bancos |
| pg_collation | Informações das collations |
| pg_namespace | Informações dos esquemas |
| pg_depend | Dependências entre objetos |
| pg_index | Informações dos índices |
| pg_class | Informações das relações |
| pg_attribute | Informações das colunas |
| pg_partitioned_table | Informações de particionamento |

Caso sejam identificadas dependências na verificação automática
das collations específicas, o script interrompe essa atualização.

Essa proteção não garante a identificação de todas as possíveis
dependências indiretas.

---

## 16. Confirmações de segurança

O script solicita autorizações durante a execução.

Exemplo:

    Confirma a manutenção? Digite SIM:

Para autorizar:

    SIM

Para cancelar:

    NAO

Também poderão ser solicitadas autorizações específicas para
atualização das versões registradas.

O cancelamento de uma etapa posterior não desfaz operações
realizadas anteriormente.

Analise todos os resultados e mantenha backups verificados
antes de autorizar a manutenção.

---

## 17. Validação manual após a manutenção

### 17.1. Verificar as versões da Collation padrão

```bash
docker exec pgsqlapi sh -c '
    psql -X \
        -U "${POSTGRES_USER:-postgres}" \
        -d postgres \
        -v ON_ERROR_STOP=1 \
        -c "
            SELECT
                datname,
                datcollversion AS versao_registrada,
                pg_database_collation_actual_version(oid)
                    AS versao_atual
            FROM pg_database
            ORDER BY datname;
        "
'
```

Exemplo de resultado no ambiente testado:

| Banco | Versão registrada | Versão atual |
|-------|-------------------|-------------|
| indices | 2.41 | 2.41 |
| postgres | 2.41 | 2.41 |
| template0 | NULL | 2.41 |
| template1 | 2.41 | 2.41 |

As versões dos bancos analisados devem coincidir quando
ambas estiverem disponíveis.

O template0 não é corrigido pelo script.

Os números das versões poderão ser diferentes em outros
ambientes.

### 17.2. Verificar as Collations específicas

```bash
for DB in postgres template1 indices; do
    echo "Banco: $DB"

    docker exec pgsqlapi sh -c '
        psql -X \
            -U "${POSTGRES_USER:-postgres}" \
            -d "$1" \
            -v ON_ERROR_STOP=1 \
            -c "
                SELECT COUNT(*) AS collations_divergentes
                FROM pg_collation
                WHERE collversion IS NOT NULL
                    AND collversion IS DISTINCT FROM
                        pg_collation_actual_version(oid);
            "
    ' sh "$DB" || break
done
```

Resultado esperado para cada banco:

    collations_divergentes
    ----------------------
                         0

Caso existam divergências, analise as causas antes de
realizar novas alterações.

### 17.3. Verificar índices inválidos

```bash
docker exec pgsqlapi sh -c '
    psql -X \
        -U "${POSTGRES_USER:-postgres}" \
        -d indices \
        -v ON_ERROR_STOP=1 \
        -c "
            SELECT
                indexrelid::regclass AS indice,
                indisvalid AS valido,
                indisready AS pronto
            FROM pg_index
            WHERE NOT indisvalid
                OR NOT indisready;
        "
'
```

Resultado esperado:

    (0 rows)

Essa consulta verifica o estado dos índices nos catálogos,
mas não constitui uma verificação completa de sua integridade
estrutural.

### 17.4. Verificar os logs

```bash
docker logs --since 10m pgsqlapi
```

O argumento --since 10m apresenta os logs dos últimos
dez minutos.

Verifique se continuam aparecendo mensagens relacionadas
a divergências de collation.

---

## 18. Restauração de backup lógico em ambiente isolado

O procedimento a seguir permite testar um backup sem modificar
o container de produção.

### 18.1. Criar um container de testes

```bash
docker run -d \
    --name pgsqlapi-teste \
    --network none \
    -e POSTGRES_USER=admin_teste \
    -e POSTGRES_PASSWORD=senha_temporaria_teste \
    -e POSTGRES_DB=postgres \
    "$(docker inspect pgsqlapi --format '{{.Image}}')"
```

### Explicação

| Argumento | Finalidade |
|-----------|------------|
| -d | Executar em segundo plano |
| --name | Definir o nome do container |
| --network none | Isolar o container da rede |
| -e | Definir variáveis de ambiente |
| docker inspect | Identificar a imagem do container original |

O container de testes não utiliza os diretórios de dados
do container de produção.

A senha apresentada é exclusivamente ilustrativa para um
ambiente isolado e temporário.

### 18.2. Verificar a disponibilidade

```bash
docker exec pgsqlapi-teste \
    pg_isready -U admin_teste -d postgres
```

Resultado esperado:

    accepting connections

### 18.3. Verificar os usuários existentes no backup

```bash
docker exec pgsqlapi grep '^CREATE ROLE ' \
    /db/backup/backup_completo_2026-11-28_150238.sql
```

O usuário administrativo temporário não deve entrar em
conflito com os usuários que serão restaurados.

### 18.4. Restaurar o backup

```bash
(
    set -o pipefail

    docker exec pgsqlapi cat \
        /db/backup/backup_completo_2026-11-28_150238.sql |
    docker exec -i pgsqlapi-teste \
        psql -X \
        -U admin_teste \
        -d postgres \
        -v ON_ERROR_STOP=1
)
```

A restauração deve ocorrer em um cluster novo e compatível.

Caso ocorra algum erro, interrompa o procedimento e analise
a mensagem apresentada.

### 18.5. Verificar as collations após a restauração

```bash
docker exec pgsqlapi-teste \
    psql -U admin_teste -d postgres -c "
        SELECT
            datname,
            datcollversion,
            pg_database_collation_actual_version(oid)
                AS versao_atual
        FROM pg_database
        ORDER BY datname;
    "
```

Durante os testes realizados, a restauração lógica em um
cluster novo eliminou as divergências de versões anteriormente
observadas.

Esse resultado não constitui uma garantia para todos os
tipos de migração ou backups.

---

## 19. Restauração de backup físico em ambiente isolado

O backup físico preserva os arquivos internos do PostgreSQL,
incluindo os índices e os metadados de collation.

Por essa razão, foi utilizado para reproduzir as divergências
existentes no ambiente original.

### 19.1. Criar um volume exclusivo para testes

```bash
docker volume create pgsqlapi-teste-fisico-dados
```

### 19.2. Verificar se o volume está vazio

```bash
docker run --rm --network none \
    -v pgsqlapi-teste-fisico-dados:/destino:ro \
    --entrypoint sh \
    "$(docker inspect pgsqlapi --format '{{.Image}}')" \
    -c 'ls -la /destino'
```

Não prossiga se o volume contiver dados que precisem
ser preservados.

### 19.3. Copiar o backup físico previamente validado

```bash
(
    set -o pipefail

    docker exec pgsqlapi \
        tar -C /db/backup/validacao_fisico_LAJsGf -cf - . |
    docker run --rm -i --network none \
        -v pgsqlapi-teste-fisico-dados:/destino \
        --entrypoint sh \
        "$(docker inspect pgsqlapi --format '{{.Image}}')" \
        -c '
            set -e

            mkdir -p /destino/pgdata

            tar -xf - -C /destino/pgdata

            chown -R postgres:postgres /destino/pgdata

            chmod 700 /destino/pgdata

            echo "Backup físico copiado com sucesso."
        '
)
```

Substitua validacao_fisico_LAJsGf pelo diretório correspondente
ao backup físico que foi extraído e validado.

### 19.4. Verificar a cópia

```bash
docker run --rm --network none \
    -v pgsqlapi-teste-fisico-dados:/destino:ro \
    --entrypoint pg_verifybackup \
    "$(docker inspect pgsqlapi --format '{{.Image}}')" \
    /destino/pgdata
```

### 19.5. Criar o container de testes

```bash
docker run -d \
    --name pgsqlapi-teste-fisico \
    --network none \
    -e POSTGRES_USER=postgres \
    -e PGDATA=/var/lib/postgresql/data/pgdata \
    -v pgsqlapi-teste-fisico-dados:/var/lib/postgresql/data \
    "$(docker inspect pgsqlapi --format '{{.Image}}')"
```

O container utiliza exclusivamente o volume de testes.

Nenhum diretório de dados do ambiente de produção é montado
nesse container.

### 19.6. Verificar a disponibilidade

```bash
docker exec pgsqlapi-teste-fisico \
    pg_isready -U postgres -d indices
```

### 19.7. Executar o script no ambiente restaurado

```bash
bash pgsqlapi/corrigir_collation.sh \
    pgsqlapi-teste-fisico indices
```

Analise os diagnósticos antes de autorizar as operações.

### 19.8. Validar o resultado

Utilize os procedimentos da seção 17, substituindo o nome
do container por pgsqlapi-teste-fisico.

---

## 20. Testes realizados em 28/11/2026

### 20.1. Ambiente utilizado

| Componente | Versão |
|------------|--------|
| PostgreSQL | 15.20 |
| Sistema operacional | Debian 13.7 Trixie |
| GLIBC | 2.41 |
| GLIBC registrada anteriormente | 2.36 |

### 20.2. Divergências das Collations específicas

Foram identificadas as seguintes divergências em cada um
dos três bancos analisados:

| Biblioteca | Versão anterior | Versão atual | Quantidade |
|------------|-----------------|-------------|------------|
| GLIBC | 2.36 | 2.41 | 2 |
| ICU | 153.120 | 153.128 | 475 |
| ICU | 153.120.42 | 153.128.46 | 331 |
| Total | | | 808 |

### 20.3. Resultado da correção

| Banco | Antes | Depois |
|-------|-------|--------|
| postgres | 808 | 0 |
| template1 | 808 | 0 |
| indices | 808 | 0 |
| Total | 2424 | 0 |

### 20.4. Preservação dos dados

Foram comparadas 77 tabelas do esquema public.

As verificações realizadas incluíram:

- Quantidade de tabelas.
- Quantidade de registros por tabela.
- Comparação do conteúdo por hashes MD5.
- Comparação entre restauração lógica e física.

Não foram identificadas diferenças nas comparações realizadas.

Esses testes não abrangem necessariamente todos os objetos,
permissões, sequências e demais componentes do PostgreSQL.

### 20.5. Teste da Collation padrão

Foi criado um banco de testes com divergência simulada:

```sql
CREATE DATABASE teste_collation
WITH TEMPLATE = template0
COLLATION_VERSION = '2.36';
```

Foi criada uma tabela com seis registros e um índice textual.

Após a execução do script:

- A versão registrada passou de 2.36 para 2.41.
- Os seis registros foram preservados.
- Os índices permaneceram válidos e prontos.
- O aviso de divergência deixou de ser apresentado.

A divergência foi simulada nos metadados.

O teste não reproduziu uma mudança real das regras de
ordenação da biblioteca GLIBC.

### 20.6. Testes funcionais

| Teste | Resultado |
|-------|-----------|
| Execução sem divergências | Aprovado |
| Restauração lógica | Aprovado |
| Verificação do backup físico | Aprovado |
| Restauração física | Aprovado |
| Correção de 2424 collations específicas | Aprovado |
| Correção da collation padrão simulada | Aprovado |
| Reconstrução dos índices de teste | Aprovado |
| Preservação dos registros comparados | Aprovado |
| Reexecução após a correção | Aprovado |
| Cancelamento da manutenção | Aprovado |
| Proteção do template0 | Aprovado |
| Validação de banco inexistente | Aprovado |
| Prevenção de bancos duplicados | Aprovado |

---

## 21. Limitações conhecidas

O script foi desenvolvido para o ambiente do projeto
api-indices e testado nos cenários descritos neste documento.

As seguintes limitações devem ser consideradas:

1. O script não realiza backups automaticamente.

2. O script não interrompe automaticamente as aplicações
   que utilizam o PostgreSQL.

3. O script não realiza restauração automática em caso de erro.

4. A verificação de dependências não garante a identificação
   de todos os objetos direta ou indiretamente afetados.

5. Algumas operações da collation padrão podem ocorrer antes
   da conclusão das verificações adicionais de segurança.

6. O REINDEX DATABASE não reconstrói todos os tipos de objetos
   dependentes nem os índices dos catálogos de sistema.

7. O template0 não é corrigido pelo script.

8. A atualização das collations ocorre separadamente em cada
   banco de dados.

9. Um erro posterior não desfaz operações anteriormente
   confirmadas em outros bancos.

10. A validação final deve ser realizada manualmente.

11. A tag postgres:15-trixie pode receber atualizações que
    alterem as versões das bibliotecas do sistema operacional.

12. Versões indisponíveis ou não registradas exigem análise
    administrativa específica.

13. Os testes não constituem uma certificação de segurança
    para todos os ambientes PostgreSQL.

O script deve ser considerado uma ferramenta assistida de
manutenção, e não um mecanismo universal de reparação.

Não execute automaticamente por cron ou durante a
inicialização do container.

---

## 22. Procedimento recomendado para novas instalações

Em uma nova máquina:

1. Clonar o repositório.
2. Verificar a configuração do Dockerfile.
3. Verificar se o diretório de dados está vazio.
4. Construir a imagem Docker.
5. Inicializar um novo cluster PostgreSQL.
6. Restaurar um backup lógico compatível.
7. Verificar as versões das collations.
8. Validar as tabelas e os registros.
9. Testar a aplicação.

A restauração lógica em um cluster novo normalmente permite
reconstruir os objetos utilizando as bibliotecas disponíveis
no novo ambiente.

Não copie indiscriminadamente o diretório físico de dados
entre ambientes diferentes.

---

## 23. Procedimento em caso de falha

Caso ocorra um erro durante a manutenção:

1. Não execute novamente o script de forma automática.
2. Mantenha as aplicações fora de operação.
3. Registre a mensagem de erro.
4. Identifique quais operações foram concluídas.
5. Verifique as versões das collations.
6. Verifique o estado dos índices.
7. Analise os objetos dependentes.
8. Avalie a necessidade de restauração.
9. Teste a recuperação em um ambiente isolado.
10. Retome a operação somente após validar o ambiente.

A restauração em produção deve ser planejada separadamente,
considerando a preservação dos dados existentes e a
compatibilidade do backup.

---

## 24. Melhorias futuras

As seguintes melhorias poderão ser implementadas posteriormente:

- Reorganização de todas as verificações de segurança para
  ocorrerem antes de qualquer alteração.
- Inclusão de um modo exclusivamente de diagnóstico.
- Validação automática após a manutenção.
- Tratamento adicional de dependências indiretas.
- Tratamento de versões de collation indisponíveis.
- Geração automática de relatórios de execução.
- Eliminação de autorizações desnecessárias quando não
  existirem divergências.
- Ampliação dos testes automatizados.

Essas melhorias não foram incorporadas à versão atual.

---

## 25. Referências oficiais

Documentação do PostgreSQL 15:

- Collation Support:
  https://www.postgresql.org/docs/15/collation.html

- ALTER COLLATION:
  https://www.postgresql.org/docs/15/sql-altercollation.html

- ALTER DATABASE:
  https://www.postgresql.org/docs/15/sql-alterdatabase.html

- REINDEX:
  https://www.postgresql.org/docs/15/sql-reindex.html

- pg_dumpall:
  https://www.postgresql.org/docs/15/app-pg-dumpall.html

- pg_basebackup:
  https://www.postgresql.org/docs/15/app-pgbasebackup.html

- pg_verifybackup:
  https://www.postgresql.org/docs/15/app-pgverifybackup.html

- Template Databases:
  https://www.postgresql.org/docs/15/manage-ag-templatedbs.html

Documentação do Docker:

- https://docs.docker.com/

Imagem oficial do PostgreSQL:

- https://hub.docker.com/_/postgres

---

## 26. Histórico

### 28/11/2026

- Alteração do Dockerfile para postgres:15-trixie.
- Desenvolvimento do script corrigir_collation.sh.
- Realização de backups lógicos e físicos.
- Validação dos backups.
- Criação de ambientes isolados de testes.
- Correção de divergências de collations específicas.
- Teste de correção da collation padrão.
- Verificação da preservação dos registros.
- Implementação de proteções adicionais.
- Elaboração da documentação de manutenção.

---

Projeto: api-indices

Última atualização: 28/11/2026
