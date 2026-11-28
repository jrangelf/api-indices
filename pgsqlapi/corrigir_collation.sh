 
 #!/bin/bash

# ============================================================
# Script: corrigir_collation.sh
# Projeto: api-indices
#
# Finalidade:
# Diagnosticar e corrigir divergências de versão de collation
# nos bancos de dados PostgreSQL executados em Docker.
# ============================================================

set -euo pipefail

# Configurações
CONTAINER="${1:-pgsqlapi}"
BANCO="${2:-indices}"

# Impedir a manutenção do banco template0
if [ "$BANCO" = "template0" ]; then
    echo "ERRO: O banco template0 não pode ser utilizado neste script."
    exit 1
fi

# Definir os bancos de dados que serão analisados
BANCOS=("postgres" "template1")

# Acrescentar o banco informado, evitando duplicidades
if [ "$BANCO" != "postgres" ] && [ "$BANCO" != "template1" ]; then
    BANCOS+=("$BANCO")
fi


echo "============================================================"
echo " MANUTENÇÃO DE COLLATION - POSTGRESQL"
echo "============================================================"
echo
echo "Container: $CONTAINER"
echo "Banco de dados: $BANCO"
echo

# Verificar se o Docker está disponível
if ! command -v docker >/dev/null 2>&1; then
    echo "ERRO: Docker não encontrado."
    exit 1
fi

# Verificar se o container está em execução
if [ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null)" != "true" ]; then
    echo "ERRO: O container $CONTAINER não está em execução ou não está acessível."
    exit 1
fi

echo "Container em execução."
echo

# Verificar a disponibilidade do PostgreSQL
if ! docker exec "$CONTAINER" pg_isready; then
    echo "ERRO: PostgreSQL não está aceitando conexões."
    exit 1
fi

# Verificar se o banco informado existe e permite conexões
BANCO_VALIDO=$(docker exec -i "$CONTAINER" sh -c '
    psql -X \
        -U "${POSTGRES_USER:-postgres}" \
        -d postgres \
        -v ON_ERROR_STOP=1 \
        -v banco="$1" \
        -A -t
' sh "$BANCO" <<'SQL'
SELECT COUNT(*)
FROM pg_database
WHERE datname = :'banco'
    AND datallowconn = true;
SQL
)

if [ "$BANCO_VALIDO" != "1" ]; then
    echo "ERRO: O banco $BANCO não existe ou não permite conexões."
    exit 1
fi

echo "Banco de dados $BANCO validado com sucesso."



echo
echo "Verificações iniciais concluídas com sucesso."

# ============================================================
# Identificar as versões do ambiente
# ============================================================

echo
echo "============================================================"
echo " VERSÕES DO AMBIENTE"
echo "============================================================"

echo
echo "Versão do PostgreSQL:"
docker exec "$CONTAINER" postgres --version

echo
echo "Sistema operacional:"
docker exec "$CONTAINER" cat /etc/os-release

echo
echo "Versão da GLIBC:"
docker exec "$CONTAINER" getconf GNU_LIBC_VERSION

echo

# ============================================================
# Consultar as versões de collation dos bancos de dados
# ============================================================

echo
echo "============================================================"
echo " VERSÕES DE COLLATION DOS BANCOS DE DADOS"
echo "============================================================"
echo

docker exec -i "$CONTAINER" sh -c '
    psql -X \
        -U "${POSTGRES_USER:-postgres}" \
        -d postgres \
        -v ON_ERROR_STOP=1
' <<'SQL'

SELECT
    datname AS banco,
    datcollversion AS versao_registrada,
    pg_database_collation_actual_version(oid) AS versao_atual,
    CASE
        WHEN datname = 'template0'
            THEN 'IGNORADO'
        WHEN datcollversion IS NULL
            THEN 'SEM VERSAO REGISTRADA'
        WHEN pg_database_collation_actual_version(oid) IS NULL
            THEN 'VERSAO ATUAL INDISPONIVEL'
        WHEN datcollversion = pg_database_collation_actual_version(oid)
            THEN 'OK'
        ELSE 'DIVERGENTE'
    END AS situacao
FROM pg_database
ORDER BY datname;

SQL

echo

# ============================================================
# Identificar os bancos que necessitam de correção
# ============================================================

echo
echo "============================================================"
echo " BANCOS QUE NECESSITAM DE CORREÇÃO"
echo "============================================================"
echo

BANCOS_DIVERGENTES=$(docker exec -i "$CONTAINER" sh -c '
    psql -X \
        -U "${POSTGRES_USER:-postgres}" \
        -d postgres \
        -v ON_ERROR_STOP=1 \
        -v banco="$1" \
        -A -t
' sh "$BANCO" <<'SQL'

SELECT datname
FROM pg_database
WHERE datname IN ('postgres', 'template1', :'banco')
    AND datname <> 'template0'
    AND datallowconn
    AND datcollversion IS NOT NULL
    AND pg_database_collation_actual_version(oid) IS NOT NULL
    AND datcollversion <> pg_database_collation_actual_version(oid)
ORDER BY datname;

SQL
)

if [ -z "$BANCOS_DIVERGENTES" ]; then
    echo "Nenhum banco necessita de correção da collation padrão."
else
    echo "Bancos com divergência de collation:"
    echo "$BANCOS_DIVERGENTES"
fi

echo

# ============================================================
# Verificar collations específicas dos bancos de dados
# ============================================================

echo
echo "============================================================"
echo " VERIFICAÇÃO DAS COLLATIONS ESPECÍFICAS"
echo "============================================================"
echo

for DB in "${BANCOS[@]}"; do
    echo "------------------------------------------------------------"
    echo "Banco de dados: $DB"
    echo "------------------------------------------------------------"

    docker exec -i "$CONTAINER" sh -c '
        psql -X \
            -U "${POSTGRES_USER:-postgres}" \
            -d "$1" \
            -v ON_ERROR_STOP=1
    ' sh "$DB" <<'SQL'

SELECT
    n.nspname AS esquema,

    CASE c.collprovider
        WHEN 'c' THEN 'GLIBC'
        WHEN 'i' THEN 'ICU'
        WHEN 'd' THEN 'PADRAO'
        ELSE 'OUTRO'
    END AS biblioteca,

    c.collversion AS versao_registrada,

    pg_collation_actual_version(c.oid) AS versao_atual,

    COUNT(*) AS quantidade

FROM pg_collation c

JOIN pg_namespace n
    ON n.oid = c.collnamespace

WHERE c.collversion IS NOT NULL
    AND c.collversion IS DISTINCT FROM
        pg_collation_actual_version(c.oid)

GROUP BY 1, 2, 3, 4

ORDER BY 1, 2, 3, 4;

SQL

    echo

done

# ============================================================
# Identificar objetos dependentes de collations divergentes
# ============================================================

echo
echo "============================================================"
echo " OBJETOS DEPENDENTES DE COLLATIONS DIVERGENTES"
echo "============================================================"
echo

for DB in "${BANCOS[@]}"; do

    echo "------------------------------------------------------------"
    echo "Banco de dados: $DB"
    echo "------------------------------------------------------------"

    docker exec -i "$CONTAINER" sh -c '
        psql -X \
            -U "${POSTGRES_USER:-postgres}" \
            -d "$1" \
            -v ON_ERROR_STOP=1
    ' sh "$DB" <<'SQL'

SELECT
    pg_describe_object(
        d.refclassid,
        d.refobjid,
        d.refobjsubid
    ) AS collation,

    pg_describe_object(
        d.classid,
        d.objid,
        d.objsubid
    ) AS objeto_dependente

FROM pg_depend d

JOIN pg_collation c
    ON d.refclassid = 'pg_collation'::regclass
    AND d.refobjid = c.oid

WHERE c.collversion IS NOT NULL
    AND c.collversion IS DISTINCT FROM
        pg_collation_actual_version(c.oid)

ORDER BY 1, 2;

SQL

    echo

done

# ============================================================
# Identificar índices que utilizam collations divergentes
# ============================================================

echo
echo "============================================================"
echo " ÍNDICES COM COLLATIONS DIVERGENTES"
echo "============================================================"
echo

for DB in "${BANCOS[@]}"; do

    echo "------------------------------------------------------------"
    echo "Banco de dados: $DB"
    echo "------------------------------------------------------------"

    docker exec -i "$CONTAINER" sh -c '
        psql -X \
            -U "${POSTGRES_USER:-postgres}" \
            -d "$1" \
            -v ON_ERROR_STOP=1
    ' sh "$DB" <<'SQL'

SELECT DISTINCT
    n.nspname AS esquema,
    t.relname AS tabela,
    i.relname AS indice,
    c.collname AS nome_collation,
    c.collversion AS versao_registrada,
    pg_collation_actual_version(c.oid) AS versao_atual

FROM pg_index idx

JOIN pg_class i
    ON i.oid = idx.indexrelid

JOIN pg_class t
    ON t.oid = idx.indrelid

JOIN pg_namespace n
    ON n.oid = t.relnamespace

JOIN pg_collation c
    ON c.oid = ANY(idx.indcollation)

WHERE c.collversion IS NOT NULL
    AND c.collversion IS DISTINCT FROM
        pg_collation_actual_version(c.oid)

ORDER BY esquema, tabela, indice, nome_collation;

SQL

    echo

done

# ============================================================
# Confirmação de segurança antes da manutenção
# ============================================================

echo
echo "============================================================"
echo " CONFIRMAÇÃO DE SEGURANÇA"
echo "============================================================"
echo

echo "As próximas operações poderão modificar o PostgreSQL."
echo
echo "Antes de continuar, certifique-se de que:"
echo
echo "1. Existe um backup atualizado e verificado."
echo "2. O procedimento de restauração é conhecido."
echo "3. As aplicações estão fora de operação."
echo "4. Existe uma janela de manutenção disponível."
echo

read -r -p "Confirma a manutenção? Digite SIM: " CONFIRMACAO

if [ "$CONFIRMACAO" != "SIM" ]; then

    echo
    echo "Manutenção cancelada pelo usuário."
    echo "Nenhuma alteração foi realizada."
    exit 0

fi

echo
echo "Manutenção autorizada pelo usuário."
echo


# ============================================================
# Reconstrução dos índices dos bancos divergentes
# ============================================================

echo
echo "============================================================"
echo " RECONSTRUÇÃO DOS ÍNDICES"
echo "============================================================"
echo

if [ -z "$BANCOS_DIVERGENTES" ]; then

    echo "Nenhum banco necessita de REINDEX por divergência da collation padrão."

else

    while IFS= read -r DB; do

        echo "------------------------------------------------------------"
        echo "Reconstruindo os índices do banco: $DB"
        echo "------------------------------------------------------------"

        docker exec -i "$CONTAINER" sh -c '
            psql -X \
                -U "${POSTGRES_USER:-postgres}" \
                -d "$1" \
                -v ON_ERROR_STOP=1 \
                -v banco="$1"
        ' sh "$DB" <<'SQL'

REINDEX DATABASE :"banco";

SQL

        echo
        echo "REINDEX concluído no banco: $DB"
        echo

    done <<< "$BANCOS_DIVERGENTES"

fi

echo

# ============================================================
# Atualizar a versão da collation padrão
# ============================================================

echo
echo "============================================================"
echo " ATUALIZAÇÃO DA COLLATION PADRÃO"
echo "============================================================"
echo

if [ -z "$BANCOS_DIVERGENTES" ]; then

    echo "Nenhum banco necessita de atualização da collation padrão."

else

    echo "Confirme que todos os objetos afetados foram verificados"
    echo "e reconstruídos quando necessário."

    read -r -p "Autoriza atualizar as versões? Digite SIM: " CONFIRMA_REFRESH

    if [ "$CONFIRMA_REFRESH" != "SIM" ]; then
        echo "Atualização das versões cancelada."
        exit 1
    fi

    while IFS= read -r DB; do

        echo "Atualizando a collation padrão do banco: $DB"

        docker exec -i "$CONTAINER" sh -c '
            psql -X \
                -U "${POSTGRES_USER:-postgres}" \
                -d "$1" \
                -v ON_ERROR_STOP=1 \
                -v banco="$1"
        ' sh "$DB" <<'SQL'

ALTER DATABASE :"banco" REFRESH COLLATION VERSION;

SQL

        echo "Versão da collation atualizada: $DB"
        echo

    done <<< "$BANCOS_DIVERGENTES"

fi

echo

# ============================================================
# Gerar comandos de atualização das collations específicas
# ============================================================

echo
echo "============================================================"
echo " COMANDOS DE ATUALIZAÇÃO DAS COLLATIONS ESPECÍFICAS"
echo "============================================================"
echo

for DB in "${BANCOS[@]}"; do

    echo "------------------------------------------------------------"
    echo "Banco de dados: $DB"
    echo "------------------------------------------------------------"

    docker exec -i "$CONTAINER" sh -c '
        psql -X \
            -U "${POSTGRES_USER:-postgres}" \
            -d "$1" \
            -v ON_ERROR_STOP=1
    ' sh "$DB" <<'SQL'

SELECT
    format(
        'ALTER COLLATION %I.%I REFRESH VERSION;',
        n.nspname,
        c.collname
    ) AS comando

FROM pg_collation c

JOIN pg_namespace n
    ON n.oid = c.collnamespace

WHERE c.collversion IS NOT NULL
    AND pg_collation_actual_version(c.oid) IS NOT NULL
    AND c.collversion <>
        pg_collation_actual_version(c.oid)

ORDER BY n.nspname, c.collname

LIMIT 5;

SQL

    echo

done


# ============================================================
# Verificar dependências adicionais das collations divergentes
# ============================================================

echo
echo "============================================================"
echo " DEPENDÊNCIAS ADICIONAIS DAS COLLATIONS"
echo "============================================================"
echo

for DB in "${BANCOS[@]}"; do

    echo "------------------------------------------------------------"
    echo "Banco de dados: $DB"
    echo "------------------------------------------------------------"

    docker exec -i "$CONTAINER" sh -c '
        psql -X \
            -U "${POSTGRES_USER:-postgres}" \
            -d "$1" \
            -v ON_ERROR_STOP=1
    ' sh "$DB" <<'SQL'

SELECT
    'COLUNA' AS tipo,
    n.nspname AS esquema,
    t.relname AS tabela,
    a.attname AS objeto,
    c.collname AS nome_collation

FROM pg_attribute a

JOIN pg_class t
    ON t.oid = a.attrelid

JOIN pg_namespace n
    ON n.oid = t.relnamespace

JOIN pg_collation c
    ON c.oid = a.attcollation

WHERE a.attnum > 0
    AND NOT a.attisdropped
    AND c.collversion IS NOT NULL
    AND c.collversion IS DISTINCT FROM
        pg_collation_actual_version(c.oid)

UNION ALL

SELECT
    'PARTICIONAMENTO' AS tipo,
    n.nspname AS esquema,
    t.relname AS tabela,
    'Chave de particionamento' AS objeto,
    c.collname AS nome_collation

FROM pg_partitioned_table p

JOIN pg_class t
    ON t.oid = p.partrelid

JOIN pg_namespace n
    ON n.oid = t.relnamespace

JOIN pg_collation c
    ON c.oid = ANY(p.partcollation)

WHERE c.collversion IS NOT NULL
    AND c.collversion IS DISTINCT FROM
        pg_collation_actual_version(c.oid)

ORDER BY 1, 2, 3, 4, 5;

SQL

    echo

done

# ============================================================
# Autorização para atualizar as collations específicas
# ============================================================

echo
echo "============================================================"
echo " AUTORIZAÇÃO PARA ATUALIZAR COLLATIONS ESPECÍFICAS"
echo "============================================================"
echo

echo "A atualização modifica as versões registradas em pg_collation."
echo
echo "O comando ALTER COLLATION REFRESH VERSION não reconstrói"
echo "índices nem corrige automaticamente objetos dependentes."
echo
echo "Confirme que:"
echo
echo "1. Os resultados dos diagnósticos foram analisados."
echo "2. Os objetos afetados foram verificados."
echo "3. Os objetos que necessitam de reconstrução foram corrigidos."
echo "4. Existe um backup atualizado e verificado."
echo

read -r -p "Autoriza atualizar as collations específicas? Digite SIM: " CONFIRMA_COLLATIONS

if [ "$CONFIRMA_COLLATIONS" != "SIM" ]; then

    echo
    echo "Atualização das collations específicas cancelada."
    exit 0

fi

echo
echo "Atualização das collations específicas autorizada."
echo

# ============================================================
# Proteção automática contra dependências
# ============================================================

echo
echo "============================================================"
echo " VERIFICAÇÃO AUTOMÁTICA DE SEGURANÇA"
echo "============================================================"
echo

for DB in "${BANCOS[@]}"; do

    echo "Verificando banco: $DB"

    TOTAL_DEPENDENCIAS=$(docker exec -i "$CONTAINER" sh -c '
        psql -X \
            -U "${POSTGRES_USER:-postgres}" \
            -d "$1" \
            -v ON_ERROR_STOP=1 \
            -A -t
    ' sh "$DB" <<'SQL'

WITH divergentes AS (

    SELECT oid
    FROM pg_collation
    WHERE collversion IS NOT NULL
        AND collversion IS DISTINCT FROM
            pg_collation_actual_version(oid)

)

SELECT

    (
        SELECT COUNT(*)
        FROM pg_depend d
        WHERE d.refclassid = 'pg_collation'::regclass
            AND d.refobjid IN (SELECT oid FROM divergentes)
    )

    +

    (
        SELECT COUNT(*)
        FROM pg_index i
        JOIN divergentes d
            ON d.oid = ANY(i.indcollation)
    )

    +

    (
        SELECT COUNT(*)
        FROM pg_attribute a
        WHERE a.attnum > 0
            AND NOT a.attisdropped
            AND a.attcollation IN (SELECT oid FROM divergentes)
    )

    +

    (
        SELECT COUNT(*)
        FROM pg_partitioned_table p
        JOIN divergentes d
            ON d.oid = ANY(p.partcollation)
    );

SQL
)

    echo "Ocorrências de dependências: $TOTAL_DEPENDENCIAS"

    if [ "$TOTAL_DEPENDENCIAS" -ne 0 ]; then

        echo
        echo "ERRO: Foram identificadas dependências no banco $DB."
        echo "Atualização das collations específicas interrompida."
        echo "É necessária uma análise manual dos objetos afetados."

        exit 1

    fi

    echo "Nenhuma dependência identificada."
    echo

done

echo "Verificação automática de segurança concluída."
echo

# ============================================================
# Atualização das collations específicas
# ============================================================

echo
echo "============================================================"
echo " ATUALIZAÇÃO DAS COLLATIONS ESPECÍFICAS"
echo "============================================================"
echo

for DB in "${BANCOS[@]}"; do

    echo "------------------------------------------------------------"
    echo "Banco de dados: $DB"
    echo "------------------------------------------------------------"

    docker exec -i "$CONTAINER" sh -c '
        psql -X \
            -U "${POSTGRES_USER:-postgres}" \
            -d "$1" \
            -v ON_ERROR_STOP=1
    ' sh "$DB" <<'SQL'

BEGIN;

SELECT
    format(
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
        pg_collation_actual_version(c.oid)

ORDER BY n.nspname, c.collname

\gexec

COMMIT;

SQL

    echo
    echo "Atualização concluída no banco: $DB"
    echo

done

echo "Atualização das collations específicas concluída."
echo