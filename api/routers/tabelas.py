"""
routers/tabelas.py
==================
Router principal da API de Índices PNRJ.

Responsabilidade:
    Define todos os endpoints HTTP GET da API, organizados em quatro grupos:

    1. Metadados e controle
       Rotas: /bcb, /descricao_tabelas, /nome_tabelas, /indexadores, /logatualizacao

    2. Indexadores BCB — séries temporais brutas coletadas via API SGS/BCB
       Rotas: /ipca, /ipca15, /inpc, /tr, /selic, /seliccopom,
              /selic_acumulada, /igpm

    3. Índices de correção monetária PNRJ (código 200–299,400-499)
       Rotas: /t200_tabela_pnrj /t408_tabela_pnrj

    4. Juros (código 300–399)
       Rotas: /t300_juros_poupanca … /t334_selic

Padrão de rotas (3 variantes por tabela/indexador):
    GET /{tabela}                — série histórica completa (order_by data ASC).
    GET /{tabela}/{mes}/{ano}    — registro único do mês/ano solicitado.
    GET /{tabela}/periodo        — intervalo via query params:
                                   mes_inicial, ano_inicial, mes_final, ano_final.

Tratamento de erros HTTP:
    400 Bad Request  — período inválido (data_inicial > data_final).
    404 Not Found    — nenhum registro; detail = NOREGS.    

Formatação de datas:
    O campo `data` (datetime) é convertido in-place para "DD/MM/YYYY" por
    formatar_data() antes de serializar qualquer resposta. Abordagem in-place
    preserva todos os outros atributos do ORM sem precisar criar dicts
    individuais — impraticável com 40+ modelos distintos.

Injeção de sessão (Dependency Injection):
    Cada request recebe sua própria sessão via get_db() + Depends.
    O padrão generator + finally garante fechamento mesmo em exceção,
    evitando vazamentos no pool do PostgreSQL.

Dependências:
    fastapi       — APIRouter, Depends, HTTPException, Path, Query
    sqlalchemy    — Session, extract
    models.py     — todos os modelos ORM (importados via *)
    database.py   — SessionLocal (fábrica de sessões)
    constantes.py — NOREGS (mensagem padrão 404)
    tools.py      — utilitários auxiliares
    debug.py      — logging global (INFO → api.log)
"""



import json
from sqlalchemy import extract, and_
from sqlalchemy.orm import Session
from sqlalchemy import desc
from starlette import status
from fastapi import APIRouter, Depends, HTTPException, Path, status, Query, Body
from database import SessionLocal, engine
from models import *
from datetime import datetime, date

from tools import *
from constantes import *
from debug import *

router = APIRouter()

# ---------------------------------------------------------------------------
# Dependência de sessão  injetada por requisição via FastAPI Depends
# ---------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Comentado: create_all é chamado em main.py. 
# Base.metadata.create_all(bind=engine)


def formatar_data(item):
    item.data = item.data.strftime("%d/%m/%Y")
    return item

def validar_busca_por_periodo(model, mes_inicial, ano_inicial, mes_final, ano_final, db):
    if ano_inicial > ano_final or (ano_inicial == ano_final and mes_inicial > mes_final):
        raise HTTPException(status_code=400, detail="Período inválido: mês/ano inicial é maior que mês/ano final")
    
    data_inicial = date(ano_inicial, mes_inicial, 1)
    data_final = date(ano_final, mes_final, 1)   

    query = (
        db.query(model)
        .filter(
            model.data >= data_inicial,
            model.data <= data_final
            )
            .order_by(model.data)        
    ) 

    data_tabela = query.all() 
    
    if data_tabela:
        data_tabela = list(map(formatar_data, data_tabela))
        return data_tabela
    
    raise HTTPException(status_code=404, detail=NOREGS)

# ROTAS

@router.get("/bcb", summary="Indexadores do Banco Central no mês corrente", tags=TAGCRL)
async def indexadores(db: Session = Depends(get_db)):
    """
    Retorna o valor mais recente de cada indexador BCB disponível.

    Consulta o último registro (maior id) de TR, SELIC, COPOM, INPC, IPCA,
    IPCA-15 e IGPM individualmente. Usa order_by(id.desc()).first() porque
    o id é chave primária  aproveita o índice primário (O(log n)).

    A função interna formatar_item usa __class__.__name__ para compor o
    rótulo dinamicamente, sem hardcode do nome de cada indexador.

    Returns:
        list[str | None]: Até 7 strings "CLASSE: DD/MM/YYYY = valor".

    Raises:
        HTTPException(404): Nenhum indexador com registros.
    """
    
    indices = []

    def formatar_item(item):
        if item is not None:
            item.data = item.data.strftime('%d/%m/%Y')
            print(f"nome da classe: {item.__class__.__name__}")
            return f"{item.__class__.__name__.upper()}: {item.data} = {item.valor}"
        return None

    s_tr = db.query(Tr).order_by(Tr.id.desc()).first()
    indices.append(formatar_item(s_tr))

    s_selic = db.query(Selic).order_by(Selic.id.desc()).first()
    indices.append(formatar_item(s_selic))

    s_copom = db.query(SelicCopom).order_by(SelicCopom.id.desc()).first()
    indices.append(formatar_item(s_copom))

    s_inpc = db.query(Inpc).order_by(Inpc.id.desc()).first()
    indices.append(formatar_item(s_inpc))

    s_ipca = db.query(Ipca).order_by(Ipca.id.desc()).first()
    indices.append(formatar_item(s_ipca))

    s_ipca15 = db.query(Ipca15).order_by(Ipca15.id.desc()).first()
    indices.append(formatar_item(s_ipca15))

    s_igpm = db.query(Igpm).order_by(Igpm.id.desc()).first()
    indices.append(formatar_item(s_igpm))

    if any(indices):
        return indices
    raise HTTPException(status_code=404, detail=NOREGS)



@router.get("/descricao_tabelas", summary="Descrição de todas as tabelas", tags=TAGCRL)
async def descricao_tabelas(db: Session = Depends(get_db)):
     """
    Retorna o catálogo completo de tabelas PNRJ, ordenado por código.

     Inclui todos os campos: codigo, nome, descricao, regra_de_calculo,
     observacao, indexador. Consumido pelo PNRJ para descoberta de tabelas
     ativas e por clientes externos para conhecer regras de cálculo.

     Returns:
         list[DescricaoTabelas]: Registros ordenados por codigo ASC.

     Raises:
         HTTPException(404): Tabela vazia.
     """
     data_tabela = db.query(DescricaoTabelas).order_by(DescricaoTabelas.codigo).all()
     if data_tabela is not None:
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


@router.get("/nome_tabelas", summary="Código, Nome e Descrição de todas as tabelas", tags=TAGCRL)
async def nome_e_codigo_das_tabelas(db: Session = Depends(get_db)):
     """
    Retorna lista simplificada das tabelas PNRJ, omitindo campos internos.

     Projeta apenas codigo, nome, descricao e observacao, omitindo
     regra_de_calculo e indexador (uso interno do PNRJ). A projeção seletiva
     reduz I/O no banco e o payload JSON retornado.

     Os resultados são convertidos de Row (NamedTuple) para dicts porque
     o FastAPI não serializa projeções parciais sem schema Pydantic.

     Returns:
         list[dict]: Chaves "codigo", "nome", "descricao", "observacao".

     Raises:
         HTTPException(404): Tabela vazia.
     """
     data_tabela = db.query(DescricaoTabelas).order_by(DescricaoTabelas.codigo).all()
          
     if data_tabela is not None:
         return [
        {
            "codigo": row.codigo,
            "nome": row.nome,
            "descricao": row.descricao
            #"observacao": row.observacao
        } 
        for row in data_tabela
        ]
     raise HTTPException(status_code=404, detail=NOREGS)


@router.get("/indexadores", summary="Indexadores do Banco Central do Brasil", tags=TAGCRL)
async def indexadores_bc(db: Session = Depends(get_db)):
     """
     Retorna todos os indexadores BCB cadastrados (código SGS, nome, descrição).

     Returns:
         list[Indexadores]: Todos os registros da tabela indexadores.

     Raises:
         HTTPException(404): Tabela vazia.
     """     

     data_tabela = db.query(Indexadores).all()
     if data_tabela is not None:
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/logatualizacao", summary="Tabela que mantém registros de atualizações", tags=TAGCRL)
async def log_atualizacao(db: Session = Depends(get_db)):
     """
     Retorna o log de atualização de todas as tabelas gerenciadas.

     Cada registro mostra data do último processamento e o flag processar:
     0 = tabela atualizada, 1 = pendente de recálculo pelo sistema PNRJ.

     Returns:
         list[LogAtualizacao]: Todos os registros.

     Raises:
         HTTPException(404): Tabela vazia.
     """     

     data_tabela = db.query(LogAtualizacao).all()
     if data_tabela is not None:
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# -----------------------------------------------------------------------------
# TABELAS DE INDEXADORES DO BANCO CENTRAL
# Cada indexador: GET /{ind}/{mes}/{ano} | GET /{ind}/periodo | GET /{ind}
# -----------------------------------------------------------------------------

# IPCA
@router.get("/ipca/{mes}/{ano}",summary=T102, tags=TAGIDX)
async def buscar_ipca_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       """
       Retorna o registro para o mês e ano especificados.

       Usa extract("year") e extract("month") para filtrar pelo mês de
       referência, independente do dia exato armazenado (sempre 1º do mês).
       .first() é suficiente: existe no máximo 1 registro por mês/tabela.

       Args:
           mes (int): Mês de referência (1-12). Validado via Path(gt=0, lt=13).
           ano (int): Ano de referência (1901-2099).
           db (Session): Sessão injetada via Depends(get_db).

       Returns:
           Objeto ORM com campo `data` formatado como "DD/MM/YYYY".

       Raises:
           HTTPException(404): Nenhum registro para o mês/ano informado.
       """

       data_tabela = (db.query(Ipca)
                      .filter(extract('year', Ipca.data) == ano, extract('month', Ipca.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/ipca/periodo",summary=T102, tags=TAGIDX)
async def buscar_ipca_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)):

    """
    Retorna registros no intervalo de meses informado.

    Delega para validar_busca_por_periodo() que filtra por objetos date
    (aproveita índice B-tree, O(log n)) em vez de extract() (full scan).

    Args:
        mes_inicial, ano_inicial: Início do período (inclusive).
        mes_final, ano_final:     Fim do período (inclusive).
        db (Session): Sessão injetada via Depends(get_db).

    Returns:
        list: Registros ORM com datas "DD/MM/YYYY", ordenados ASC.

    Raises:
        HTTPException(400): Período inválido (início > fim).
        HTTPException(404): Nenhum registro no período.
    """

    return validar_busca_por_periodo(Ipca, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/ipca", summary=T102, tags=TAGIDX)
async def indexador_ipca(db: Session = Depends(get_db)):
     """
     Retorna a série histórica completa, ordenada cronologicamente.

     Returns:
         list: Todos os registros com `data` formatada "DD/MM/YYYY", ASC.

     Raises:
         HTTPException(404): Tabela vazia.
     """     

     data_tabela = db.query(Ipca).order_by(Ipca.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# IPCA-15
@router.get("/ipca15/{mes}/{ano}", summary=T110, tags=TAGIDX)
async def buscar_ipca15_pelo_mes_e_ano(
    mes: int = Path(title="Mês", gt=0,lt=13),
    ano: int = Path(title="Ano", gt=1900,lt=2100),
    db: Session = Depends(get_db)):       
       
       data_tabela = (db.query(Ipca15)
                      .filter(extract('year', Ipca15.data) == ano, extract('month', Ipca15.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/ipca15/periodo", summary=T110, tags=TAGIDX)
async def buscar_ipca15_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)):

    return validar_busca_por_periodo(Ipca15, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/ipca15", summary=T110, tags=TAGIDX)
async def indexador_ipca15(db: Session = Depends(get_db)):
     data_tabela = db.query(Ipca15).order_by(Ipca15.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)

# INPC
@router.get("/inpc/{mes}/{ano}", summary=T100, tags=TAGIDX)
async def buscar_inpc_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(Inpc)
                      .filter(extract('year', Inpc.data) == ano, extract('month', Inpc.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/inpc/periodo", summary=T100, tags=TAGIDX)
async def buscar_inpc_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(Inpc, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/inpc", summary=T100, tags=TAGIDX)
async def indexador_inpc(db: Session = Depends(get_db)):
     data_tabela = db.query(Inpc).order_by(Inpc.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TR
@router.get("/tr/{mes}/{ano}", summary=T104, tags=TAGIDX)
async def buscar_tr_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(Tr)
                      .filter(extract('year', Tr.data) == ano, extract('month', Tr.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)


@router.get("/tr/periodo", summary=T104, tags=TAGIDX)
async def buscar_tr_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(Tr, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/tr", summary=T104, tags=TAGIDX)
async def indexador_tr(db: Session = Depends(get_db)):
     data_tabela = db.query(Tr).order_by(Tr.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TXLEGAL
@router.get("/txlegal/{mes}/{ano}", summary=T114, tags=TAGIDX)
async def buscar_txlegal_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=2000,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(TxLegal)
                      .filter(extract('year', TxLegal.data) == ano, extract('month', TxLegal.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)


@router.get("/txlegal/periodo", summary=T114, tags=TAGIDX)
async def buscar_txlegal_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=2000, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=2000, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(TxLegal, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/txlegal", summary=T114, tags=TAGIDX)
async def indexador_txlegal(db: Session = Depends(get_db)):
     data_tabela = db.query(TxLegal).order_by(TxLegal.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# SELIC
@router.get("/selic/{mes}/{ano}", summary=T106, tags=TAGIDX)
async def buscar_selic_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(Selic)
                      .filter(extract('year', Selic.data) == ano, extract('month', Selic.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/selic/periodo", summary=T106, tags=TAGIDX)
async def buscar_selic_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(Selic, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/selic", summary=T106, tags=TAGIDX)
async def indexador_selic(db: Session = Depends(get_db)):
     data_tabela = db.query(Selic).order_by(Selic.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# SELIC COPOM
@router.get("/seliccopom/{mes}/{ano}", summary=T108, tags=TAGIDX)
async def buscar_copom_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(SelicCopom)
                      .filter(extract('year', SelicCopom.data) == ano, extract('month', SelicCopom.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/seliccopom/periodo", summary=T108, tags=TAGIDX)
async def buscar_copom_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(SelicCopom, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/seliccopom", summary=T108, tags=TAGIDX)
async def indexador_selic_copom(db: Session = Depends(get_db)):
     data_tabela = db.query(SelicCopom).order_by(SelicCopom.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)

#SELIC Acumulada
@router.get("/selic_acumulada/{mes}/{ano}", summary=T107, tags=TAGIDX)
async def buscar_selic_acm_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
     data_tabela = (db.query(T312Selic)
                      .filter(extract('year', T312Selic.data) == ano, extract('month', T312Selic.data) == mes)
                      .first()
                      )
     if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# IGPM
@router.get("/igpm/{mes}/{ano}", summary=T112, tags=TAGIDX)
async def buscar_igpm_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(Igpm)
                      .filter(extract('year', Igpm.data) == ano, extract('month', Igpm.data) == mes)
                      .first()
                      )
       if data_tabela is not None:            
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/igpm/periodo", summary=T112, tags=TAGIDX)
async def buscar_igpm_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)):

    return validar_busca_por_periodo(Igpm, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/igpm", summary=T112, tags=TAGIDX)
async def indexador_igpm(db: Session = Depends(get_db)):
     data_tabela = db.query(Igpm).order_by(Igpm.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)

# ----------------------------------------------------------------------------------
# TABELAS DE ÍNDICES PNRJ de débitos (200-299)
# Campos: id, data, indexador, variacao_mensal, 
# numero_indice, fator_vigente, indice_correcao
# ----------------------------------------------------------------------------------

# TABELA t200 ---------------------------------------------------------------------- 
@router.get("/t200_tabela_pnrj/{mes}/{ano}", summary=T200, tags=TAGDBT)
async def t200_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T200TabelaPnrj)
                      .filter(extract('year', T200TabelaPnrj.data) == ano, 
                              extract('month', T200TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t200_tabela_pnrj/periodo", summary=T200, tags=TAGDBT)
async def t200_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T200TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t200_tabela_pnrj", summary=T200, tags=TAGDBT)
async def t200_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T200TabelaPnrj).order_by(T200TabelaPnrj.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t202 ----------------------------------------------------------------------
@router.get("/t202_tabela_pnrj/{mes}/{ano}", summary=T202, tags=TAGDBT)
async def t202_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T202TabelaPnrj)
                      .filter(extract('year', T202TabelaPnrj.data) == ano, 
                              extract('month', T202TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t202_tabela_pnrj/periodo", summary=T202, tags=TAGDBT)
async def t202_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)):

    return validar_busca_por_periodo(T202TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t202_tabela_pnrj", summary=T202, tags=TAGDBT)
async def t202_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T202TabelaPnrj).order_by(T202TabelaPnrj.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t204 ---------------------------------------------------------------------- 
@router.get("/t204_tabela_pnrj/{mes}/{ano}", summary=T204, tags=TAGDBT)
async def t204_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T204TabelaPnrj)
                      .filter(extract('year', T204TabelaPnrj.data) == ano, 
                              extract('month', T204TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t204_tabela_pnrj/periodo", summary=T204, tags=TAGDBT)
async def t204_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T204TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t204_tabela_pnrj", summary=T204, tags=TAGDBT)
async def t204_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T204TabelaPnrj).order_by(T204TabelaPnrj.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t206 ---------------------------------------------------------------------- 
@router.get("/t206_tabela_pnrj/{mes}/{ano}", summary=T206, tags=TAGDBT)
async def t206_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T206TabelaPnrj)
                      .filter(extract('year', T206TabelaPnrj.data) == ano, 
                              extract('month', T206TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t206_tabela_pnrj/periodo", summary=T206, tags=TAGDBT)
async def t206_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T206TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t206_tabela_pnrj", summary=T206, tags=TAGDBT)
async def t206_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T206TabelaPnrj).order_by(T206TabelaPnrj.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t208 ---------------------------------------------------------------------- 
@router.get("/t208_tabela_pnrj/{mes}/{ano}", summary=T208, tags=TAGDBT)
async def t208_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T208TabelaPnrj)
                      .filter(extract('year', T208TabelaPnrj.data) == ano, 
                              extract('month', T208TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t208_tabela_pnrj/periodo", summary=T208, tags=TAGDBT)
async def t208_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):

    return validar_busca_por_periodo(T208TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t208_tabela_pnrj", summary=T208, tags=TAGDBT)
async def t208_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T208TabelaPnrj).order_by(T208TabelaPnrj.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t210 ---------------------------------------------------------------------- 
@router.get("/t210_tabela_pnrj/{mes}/{ano}", summary=T210, tags=TAGDBT)
async def t210_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T210TabelaPnrj)
                      .filter(extract('year', T210TabelaPnrj.data) == ano, 
                              extract('month', T210TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t210_tabela_pnrj/periodo", summary=T210, tags=TAGDBT)
async def t210_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T210TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t210_tabela_pnrj", summary=T210, tags=TAGDBT)
async def t210_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T210TabelaPnrj).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)
					

# TABELA t212 ---------------------------------------------------------------------- 
@router.get("/t212_tabela_pnrj/{mes}/{ano}", summary=T212, tags=TAGDBT)
async def t212_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T212TabelaPnrj)
                      .filter(extract('year', T212TabelaPnrj.data) == ano, 
                              extract('month', T212TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t212_tabela_pnrj/periodo", summary=T212, tags=TAGDBT)
async def t212_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T212TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t212_tabela_pnrj", summary=T212, tags=TAGDBT)
async def t212_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T212TabelaPnrj).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t214 ---------------------------------------------------------------------- 
@router.get("/t214_tabela_pnrj/{mes}/{ano}", summary=T214, tags=TAGDBT)
async def t214_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T214TabelaPnrj)
                      .filter(extract('year', T214TabelaPnrj.data) == ano, 
                              extract('month', T214TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t214_tabela_pnrj/periodo", summary=T214, tags=TAGDBT)
async def t214_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T214TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t214_tabela_pnrj", summary=T214, tags=TAGDBT)
async def t214_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T214TabelaPnrj).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t216 ---------------------------------------------------------------------- 
@router.get("/t216_tabela_pnrj/{mes}/{ano}", summary=T216, tags=TAGDBT)
async def t216_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T216TabelaPnrj)
                      .filter(extract('year', T216TabelaPnrj.data) == ano, 
                              extract('month', T216TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t216_tabela_pnrj/periodo", summary=T216, tags=TAGDBT)
async def t216_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T216TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t216_tabela_pnrj", summary=T216, tags=TAGDBT)
async def t216_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T216TabelaPnrj).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t218 ---------------------------------------------------------------------- 
@router.get("/t218_tabela_pnrj/{mes}/{ano}", summary=T218, tags=TAGDBT)
async def t218_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T218TabelaPnrj)
                      .filter(extract('year', T218TabelaPnrj.data) == ano, 
                              extract('month', T218TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t218_tabela_pnrj/periodo", summary=T218, tags=TAGDBT)
async def t218_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T218TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t218_tabela_pnrj", summary=T218, tags=TAGDBT)
async def t218_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T218TabelaPnrj).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t220 ---------------------------------------------------------------------- 
@router.get("/t220_tabela_pnrj/{mes}/{ano}", summary=T220, tags=TAGDBT)
async def t220_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T220TabelaPnrj)
                      .filter(extract('year', T220TabelaPnrj.data) == ano, 
                              extract('month', T220TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t220_tabela_pnrj/periodo", summary=T220, tags=TAGDBT)
async def t220_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T220TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t220_tabela_pnrj", summary=T220, tags=TAGDBT)
async def t220_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T220TabelaPnrj).order_by((T220TabelaPnrj.data)).all()
     #data_tabela = db.query(T220TabelaPnrj).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t222 ---------------------------------------------------------------------- 
@router.get("/t222_tabela_pnrj/{mes}/{ano}", summary=T222, tags=TAGDBT)
async def t222_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T222TabelaPnrj)
                      .filter(extract('year', T222TabelaPnrj.data) == ano, 
                              extract('month', T222TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t222_tabela_pnrj/periodo", summary=T222, tags=TAGDBT)
async def t222_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T222TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t222_tabela_pnrj", summary=T222, tags=TAGDBT)
async def t222_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T222TabelaPnrj).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t224 ---------------------------------------------------------------------- 
@router.get("/t224_tabela_pnrj/{mes}/{ano}", summary=T224, tags=TAGDBT)
async def t224_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T224TabelaPnrj)
                      .filter(extract('year', T224TabelaPnrj.data) == ano, 
                              extract('month', T224TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t224_tabela_pnrj/periodo", summary=T224, tags=TAGDBT)
async def t224_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T224TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t224_tabela_pnrj", summary=T224, tags=TAGDBT)
async def t224_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T224TabelaPnrj).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t226 ---------------------------------------------------------------------- 
@router.get("/t226_tabela_pnrj/{mes}/{ano}", summary=T226, tags=TAGDBT)
async def t226_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T226TabelaPnrj)
                      .filter(extract('year', T226TabelaPnrj.data) == ano, 
                              extract('month', T226TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t226_tabela_pnrj/periodo", summary=T226, tags=TAGDBT)
async def t226_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T226TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t226_tabela_pnrj", summary=T226, tags=TAGDBT)
async def t226_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T226TabelaPnrj).order_by(T226TabelaPnrj.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t228 ---------------------------------------------------------------------- 
@router.get("/t228_tabela_pnrj/{mes}/{ano}", summary=T228, tags=TAGDBT)
async def t228_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T228TabelaPnrj)
                      .filter(extract('year', T228TabelaPnrj.data) == ano, 
                              extract('month', T228TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t228_tabela_pnrj/periodo", summary=T228, tags=TAGDBT)
async def t228_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T228TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t228_tabela_pnrj", summary=T228, tags=TAGDBT)
async def t228_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T228TabelaPnrj).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t230 ---------------------------------------------------------------------- 
@router.get("/t230_tabela_pnrj/{mes}/{ano}", summary=T230, tags=TAGDBT)
async def t230_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T230TabelaPnrj)
                      .filter(extract('year', T230TabelaPnrj.data) == ano, 
                              extract('month', T230TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t230_tabela_pnrj/periodo", summary=T230, tags=TAGDBT)
async def t230_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T230TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t230_tabela_pnrj", summary=T230, tags=TAGDBT)
async def t230_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T230TabelaPnrj).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)

# TABELA t232 ---------------------------------------------------------------------- 
@router.get("/t232_tabela_pnrj/{mes}/{ano}", summary=T232, tags=TAGDBT)
async def t232_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T232TabelaPnrj)
                      .filter(extract('year', T232TabelaPnrj.data) == ano, 
                              extract('month', T232TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t232_tabela_pnrj/periodo", summary=T232, tags=TAGDBT)
async def t232_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T232TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t232_tabela_pnrj", summary=T232, tags=TAGDBT)
async def t232_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T232TabelaPnrj).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)

# TABELA t234 ---------------------------------------------------------------------- 
@router.get("/t234_tabela_pnrj/{mes}/{ano}", summary=T234, tags=TAGDBT)
async def t234_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T234TabelaPnrj)
                      .filter(extract('year', T234TabelaPnrj.data) == ano, 
                              extract('month', T234TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t234_tabela_pnrj/periodo", summary=T234, tags=TAGDBT)
async def t234_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T234TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t234_tabela_pnrj", summary=T234, tags=TAGDBT)
async def t234_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T234TabelaPnrj).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)



# TABELA t236 ---------------------------------------------------------------------- 
@router.get("/t236_tabela_pnrj/{mes}/{ano}", summary=T236, tags=TAGDBT)
async def t236_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T236TabelaPnrj)
                      .filter(extract('year', T236TabelaPnrj.data) == ano, 
                              extract('month', T236TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t236_tabela_pnrj/periodo", summary=T236, tags=TAGDBT)
async def t236_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T236TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t236_tabela_pnrj", summary=T236, tags=TAGDBT)
async def t236_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T236TabelaPnrj).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t238 ---------------------------------------------------------------------- 
@router.get("/t238_tabela_pnrj/{mes}/{ano}", summary=T238, tags=TAGDBT)
async def t238_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T236TabelaPnrj)
                      .filter(extract('year', T238TabelaPnrj.data) == ano, 
                              extract('month', T238TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t238_tabela_pnrj/periodo", summary=T238, tags=TAGDBT)
async def t238_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T238TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t238_tabela_pnrj", summary=T238, tags=TAGDBT)
async def t238_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T238TabelaPnrj).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)



# ------------------------------------------------------------
#  incluídas pela EC136
# ------------------------------------------------------------

# TABELA t240 ---------------------------------------------------------------------- 
@router.get("/t240_tabela_pnrj/{mes}/{ano}", summary=T240, tags=TAGDBT)
async def t240_tabela_pnrj_pelo_mes_e_ano(
    mes: int = Path(title="Mês", gt=0, lt=13),
    ano: int = Path(title="Ano", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    data_tabela = (
        db.query(T240TabelaPnrj)
        .filter(
            extract('year', T240TabelaPnrj.data) == ano,
            extract('month', T240TabelaPnrj.data) == mes
        )
        .first()
    )
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)


@router.get("/t240_tabela_pnrj/periodo", summary=T240, tags=TAGDBT)
async def t240_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(
        T240TabelaPnrj,
        mes_inicial,
        ano_inicial,
        mes_final,
        ano_final,
        db
    )


@router.get("/t240_tabela_pnrj", summary=T240, tags=TAGDBT)
async def t240_tabela_pnrj(db: Session = Depends(get_db)):
    #data_tabela = db.query(T240TabelaPnrj).all()
    data_tabela = db.query(T240TabelaPnrj).order_by(T240TabelaPnrj.id).all()

    if data_tabela:        
        data_tabela = list(map(formatar_data, data_tabela))
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)

from sqlalchemy import text

'''
@router.get("/debug_t240", tags=TAGDBT)
async def debug_t240(db: Session = Depends(get_db)):
    regs = db.query(T240TabelaPnrj).all()
    return {
        "banco": str(db.bind.url).split("@")[-1],   # host/banco, sem a senha
        "count_sql": db.execute(text("SELECT COUNT(*) FROM t240_tabela_pnrj")).scalar(),
        "count_orm": len(regs),
        "ultimo_id": regs[-1].id if regs else None,
        "formatado_ultimo": str(formatar_data(regs[-1])) if regs else None,
    }
'''

# TABELA t242 ---------------------------------------------------------------------- 
@router.get("/t242_tabela_pnrj/{mes}/{ano}", summary=T242, tags=TAGDBT)
async def t242_tabela_pnrj_pelo_mes_e_ano(
    mes: int = Path(title="Mês", gt=0, lt=13),
    ano: int = Path(title="Ano", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    data_tabela = (
        db.query(T242TabelaPnrj)
        .filter(
            extract('year', T242TabelaPnrj.data) == ano,
            extract('month', T242TabelaPnrj.data) == mes
        )
        .first()
    )
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)


@router.get("/t242_tabela_pnrj/periodo", summary=T242, tags=TAGDBT)
async def t242_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(
        T242TabelaPnrj,
        mes_inicial,
        ano_inicial,
        mes_final,
        ano_final,
        db
    )


@router.get("/t242_tabela_pnrj", summary=T242, tags=TAGDBT)
async def t242_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T242TabelaPnrj).all()
    if data_tabela:
        data_tabela = list(map(formatar_data, data_tabela))
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t244 ---------------------------------------------------------------------- 
@router.get("/t244_tabela_pnrj/{mes}/{ano}", summary=T244, tags=TAGDBT)
async def t244_tabela_pnrj_pelo_mes_e_ano(
    mes: int = Path(title="Mês", gt=0, lt=13),
    ano: int = Path(title="Ano", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    data_tabela = (
        db.query(T244TabelaPnrj)
        .filter(
            extract('year', T244TabelaPnrj.data) == ano,
            extract('month', T244TabelaPnrj.data) == mes
        )
        .first()
    )
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)


@router.get("/t244_tabela_pnrj/periodo", summary=T244, tags=TAGDBT)
async def t244_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(
        T244TabelaPnrj,
        mes_inicial,
        ano_inicial,
        mes_final,
        ano_final,
        db
    )

@router.get("/t244_tabela_pnrj", summary=T244, tags=TAGDBT)
async def t244_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T244TabelaPnrj).all()
    if data_tabela:
        data_tabela = list(map(formatar_data, data_tabela))
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t246 ---------------------------------------------------------------------- 
@router.get("/t246_tabela_pnrj/{mes}/{ano}", summary=T246, tags=TAGDBT)
async def t246_tabela_pnrj_pelo_mes_e_ano(
    mes: int = Path(title="Mês", gt=0, lt=13),
    ano: int = Path(title="Ano", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    data_tabela = (
        db.query(T246TabelaPnrj)
        .filter(
            extract('year', T246TabelaPnrj.data) == ano,
            extract('month', T246TabelaPnrj.data) == mes
        )
        .first()
    )
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)


@router.get("/t246_tabela_pnrj/periodo", summary=T246, tags=TAGDBT)
async def t246_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(
        T246TabelaPnrj,
        mes_inicial,
        ano_inicial,
        mes_final,
        ano_final,
        db
    )


@router.get("/t246_tabela_pnrj", summary=T246, tags=TAGDBT)
async def t246_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T246TabelaPnrj).all()
    if data_tabela:
        data_tabela = list(map(formatar_data, data_tabela))
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)



# TABELA t248 ---------------------------------------------------------------------- 
@router.get("/t248_tabela_pnrj/{mes}/{ano}", summary=T248, tags=TAGDBT)
async def t248_tabela_pnrj_pelo_mes_e_ano(
    mes: int = Path(title="Mês", gt=0, lt=13),
    ano: int = Path(title="Ano", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    data_tabela = (
        db.query(T248TabelaPnrj)
        .filter(
            extract('year', T248TabelaPnrj.data) == ano,
            extract('month', T248TabelaPnrj.data) == mes
        )
        .first()
    )
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)


@router.get("/t248_tabela_pnrj/periodo", summary=T248, tags=TAGDBT)
async def t248_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(
        T248TabelaPnrj,
        mes_inicial,
        ano_inicial,
        mes_final,
        ano_final,
        db
    )


@router.get("/t248_tabela_pnrj", summary=T248, tags=TAGDBT)
async def t248_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T248TabelaPnrj).all()
    if data_tabela:
        data_tabela = list(map(formatar_data, data_tabela))
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t250 ---------------------------------------------------------------------- 
@router.get("/t250_tabela_pnrj/{mes}/{ano}", summary=T250, tags=TAGDBT)
async def t250_tabela_pnrj_pelo_mes_e_ano(
    mes: int = Path(title="Mês", gt=0, lt=13),
    ano: int = Path(title="Ano", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    data_tabela = (
        db.query(T250TabelaPnrj)
        .filter(
            extract('year', T250TabelaPnrj.data) == ano,
            extract('month', T250TabelaPnrj.data) == mes
        )
        .first()
    )
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)


@router.get("/t250_tabela_pnrj/periodo", summary=T250, tags=TAGDBT)
async def t250_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(
        T250TabelaPnrj,
        mes_inicial,
        ano_inicial,
        mes_final,
        ano_final,
        db
    )


@router.get("/t250_tabela_pnrj", summary=T250, tags=TAGDBT)
async def t250_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T250TabelaPnrj).all()
    if data_tabela:        
        data_tabela = list(map(formatar_data, data_tabela))
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)




# TABELA t252 ---------------------------------------------------------------------- 
@router.get("/t252_tabela_pnrj/{mes}/{ano}", summary=T252, tags=TAGDBT)
async def t252_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0, lt=13),
                                          ano: int = Path(title="Ano", gt=1900, lt=2100),
                                          db: Session = Depends(get_db)):
    data_tabela = (db.query(T252TabelaPnrj)
                   .filter(extract('year', T252TabelaPnrj.data) == ano,
                           extract('month', T252TabelaPnrj.data) == mes)
                   .first())
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t252_tabela_pnrj/periodo", summary=T252, tags=TAGDBT)
async def t252_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T252TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t252_tabela_pnrj", summary=T252, tags=TAGDBT)
async def t252_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T252TabelaPnrj).all()
    if data_tabela:
        return list(map(formatar_data, data_tabela))
    raise HTTPException(status_code=404, detail=NOREGS)



# TABELA t254 ---------------------------------------------------------------------- 
@router.get("/t254_tabela_pnrj/{mes}/{ano}", summary=T254, tags=TAGDBT)
async def t254_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0, lt=13),
                                          ano: int = Path(title="Ano", gt=1900, lt=2100),
                                          db: Session = Depends(get_db)):
    data_tabela = (db.query(T254TabelaPnrj)
                   .filter(extract('year', T254TabelaPnrj.data) == ano,
                           extract('month', T254TabelaPnrj.data) == mes)
                   .first())
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t254_tabela_pnrj/periodo", summary=T254, tags=TAGDBT)
async def t254_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T254TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t254_tabela_pnrj", summary=T254, tags=TAGDBT)
async def t254_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T254TabelaPnrj).all()
    if data_tabela:
        return list(map(formatar_data, data_tabela))
    raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t256 ---------------------------------------------------------------------- 
@router.get("/t256_tabela_pnrj/{mes}/{ano}", summary=T256, tags=TAGDBT)
async def t256_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0, lt=13),
                                          ano: int = Path(title="Ano", gt=1900, lt=2100),
                                          db: Session = Depends(get_db)):
    data_tabela = (db.query(T256TabelaPnrj)
                   .filter(extract('year', T256TabelaPnrj.data) == ano,
                           extract('month', T256TabelaPnrj.data) == mes)
                   .first())
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t256_tabela_pnrj/periodo", summary=T256, tags=TAGDBT)
async def t256_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T256TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t256_tabela_pnrj", summary=T256, tags=TAGDBT)
async def t256_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T256TabelaPnrj).all()
    if data_tabela:
        return list(map(formatar_data, data_tabela))
    raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t258 ---------------------------------------------------------------------- 
@router.get("/t258_tabela_pnrj/{mes}/{ano}", summary=T258, tags=TAGDBT)
async def t258_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0, lt=13),
                                          ano: int = Path(title="Ano", gt=1900, lt=2100),
                                          db: Session = Depends(get_db)):
    data_tabela = (db.query(T258TabelaPnrj)
                   .filter(extract('year', T258TabelaPnrj.data) == ano,
                           extract('month', T258TabelaPnrj.data) == mes)
                   .first())
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t258_tabela_pnrj/periodo", summary=T258, tags=TAGDBT)
async def t258_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T258TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t258_tabela_pnrj", summary=T258, tags=TAGDBT)
async def t258_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T258TabelaPnrj).all()
    if data_tabela:
        return list(map(formatar_data, data_tabela))
    raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t260 ---------------------------------------------------------------------- 
@router.get("/t260_tabela_pnrj/{mes}/{ano}", summary=T260, tags=TAGDBT)
async def t260_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0, lt=13),
                                          ano: int = Path(title="Ano", gt=1900, lt=2100),
                                          db: Session = Depends(get_db)):
    data_tabela = (db.query(T260TabelaPnrj)
                   .filter(extract('year', T260TabelaPnrj.data) == ano,
                           extract('month', T260TabelaPnrj.data) == mes)
                   .first())
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t260_tabela_pnrj/periodo", summary=T260, tags=TAGDBT)
async def t260_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T260TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t260_tabela_pnrj", summary=T260, tags=TAGDBT)
async def t260_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T260TabelaPnrj).all()
    if data_tabela:
        return list(map(formatar_data, data_tabela))
    raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t262 ---------------------------------------------------------------------- 
@router.get("/t262_tabela_pnrj/{mes}/{ano}", summary=T262, tags=TAGDBT)
async def t262_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0, lt=13),
                                          ano: int = Path(title="Ano", gt=1900, lt=2100),
                                          db: Session = Depends(get_db)):
    data_tabela = (db.query(T262TabelaPnrj)
                   .filter(extract('year', T262TabelaPnrj.data) == ano,
                           extract('month', T262TabelaPnrj.data) == mes)
                   .first())
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t262_tabela_pnrj/periodo", summary=T262, tags=TAGDBT)
async def t262_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T262TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t262_tabela_pnrj", summary=T262, tags=TAGDBT)
async def t262_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T262TabelaPnrj).all()
    if data_tabela:
        return list(map(formatar_data, data_tabela))
    raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t264 ---------------------------------------------------------------------- 
@router.get("/t264_tabela_pnrj/{mes}/{ano}", summary=T264, tags=TAGDBT)
async def t264_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0, lt=13),
                                          ano: int = Path(title="Ano", gt=1900, lt=2100),
                                          db: Session = Depends(get_db)):
    data_tabela = (db.query(T264TabelaPnrj)
                   .filter(extract('year', T264TabelaPnrj.data) == ano,
                           extract('month', T264TabelaPnrj.data) == mes)
                   .first())
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t264_tabela_pnrj/periodo", summary=T264, tags=TAGDBT)
async def t264_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T264TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t264_tabela_pnrj", summary=T264, tags=TAGDBT)
async def t264_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T264TabelaPnrj).all()
    if data_tabela:
        return list(map(formatar_data, data_tabela))
    raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t266 ---------------------------------------------------------------------- 
@router.get("/t266_tabela_pnrj/{mes}/{ano}", summary=T266, tags=TAGDBT)
async def t266_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0, lt=13),
                                          ano: int = Path(title="Ano", gt=1900, lt=2100),
                                          db: Session = Depends(get_db)):
    data_tabela = (db.query(T266TabelaPnrj)
                   .filter(extract('year', T266TabelaPnrj.data) == ano,
                           extract('month', T266TabelaPnrj.data) == mes)
                   .first())
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t266_tabela_pnrj/periodo", summary=T266, tags=TAGDBT)
async def t266_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T266TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t266_tabela_pnrj", summary=T266, tags=TAGDBT)
async def t266_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T266TabelaPnrj).all()
    if data_tabela:
        return list(map(formatar_data, data_tabela))
    raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t268 ---------------------------------------------------------------------- 
@router.get("/t268_tabela_pnrj/{mes}/{ano}", summary=T268, tags=TAGDBT)
async def t268_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0, lt=13),
                                          ano: int = Path(title="Ano", gt=1900, lt=2100),
                                          db: Session = Depends(get_db)):
    data_tabela = (db.query(T268TabelaPnrj)
                   .filter(extract('year', T268TabelaPnrj.data) == ano,
                           extract('month', T268TabelaPnrj.data) == mes)
                   .first())
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t268_tabela_pnrj/periodo", summary=T268, tags=TAGDBT)
async def t268_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T268TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t268_tabela_pnrj", summary=T268, tags=TAGDBT)
async def t268_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T268TabelaPnrj).all()
    if data_tabela:
        return list(map(formatar_data, data_tabela))
    raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t270 ---------------------------------------------------------------------- 
@router.get("/t270_tabela_pnrj/{mes}/{ano}", summary=T270, tags=TAGDBT)
async def t270_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0, lt=13),
                                          ano: int = Path(title="Ano", gt=1900, lt=2100),
                                          db: Session = Depends(get_db)):
    data_tabela = (db.query(T270TabelaPnrj)
                   .filter(extract('year', T270TabelaPnrj.data) == ano,
                           extract('month', T270TabelaPnrj.data) == mes)
                   .first())
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t270_tabela_pnrj/periodo", summary=T270, tags=TAGDBT)
async def t270_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T270TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t270_tabela_pnrj", summary=T270, tags=TAGDBT)
async def t270_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T270TabelaPnrj).all()
    if data_tabela:
        data_tabela = list(map(formatar_data, data_tabela))
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)



# ----------------------------------------------------------------------------------
# TABELAS DE JUROS (300-319) - Débitos
# 300: Poupança | 302-310: derivados | 310PNN: uso específico
# 312: SELIC acumulada | 
# ----------------------------------------------------------------------------------

# TABELA t300 ---------------------------------------------------------------------- 
@router.get("/t300_juros_poupanca/{mes}/{ano}", summary=T300, tags=TAGJDEB)
async def t300_juros_poupanca_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T300Juros)
                      .filter(extract('year', T300Juros.data) == ano, 
                              extract('month', T300Juros.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t300_juros_poupanca/periodo", summary=T300, tags=TAGJDEB)
async def t300_juros_poupanca_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T300Juros,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t300_juros_poupanca", summary=T300, tags=TAGJDEB)
async def t300_juros_poupanca(db: Session = Depends(get_db)):
     data_tabela = db.query(T300Juros).order_by(T300Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t302 ---------------------------------------------------------------------- 
@router.get("/t302_juros/{mes}/{ano}", summary=T302, tags=TAGJDEB)
async def t302_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T302Juros)
                      .filter(extract('year', T302Juros.data) == ano, 
                              extract('month', T302Juros.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t302_juros/periodo", summary=T302, tags=TAGJDEB)
async def t302_juros_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T302Juros,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t302_juros", summary=T302, tags=TAGJDEB)
async def t302_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T302Juros).order_by(T302Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t304 ---------------------------------------------------------------------- 
@router.get("/t304_juros/{mes}/{ano}", summary=T304, tags=TAGJDEB)
async def t304_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T304Juros)
                      .filter(extract('year', T304Juros.data) == ano, 
                              extract('month', T304Juros.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t304_juros/periodo", summary=T304, tags=TAGJDEB)
async def t304_juros_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T304Juros,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t304_juros", summary=T304, tags=TAGJDEB)
async def t304_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T304Juros).order_by(T304Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t306 ---------------------------------------------------------------------- 
@router.get("/t306_juros/{mes}/{ano}", summary=T306, tags=TAGJDEB)
async def t306_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T306Juros)
                      .filter(extract('year', T306Juros.data) == ano, 
                              extract('month', T306Juros.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t306_juros/periodo", summary=T306, tags=TAGJDEB)
async def t306_juros_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T306Juros,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t306_juros", summary=T306, tags=TAGJDEB)
async def t306_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T306Juros).order_by(T306Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t308 ---------------------------------------------------------------------- 
@router.get("/t308_juros/{mes}/{ano}", summary=T308, tags=TAGJDEB)
async def t308_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T308Juros)
                      .filter(extract('year', T308Juros.data) == ano, 
                              extract('month', T308Juros.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t308_juros/periodo", summary=T308, tags=TAGJDEB)
async def t308_juros_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T308Juros,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t308_juros", summary=T308, tags=TAGJDEB)
async def t308_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T308Juros).order_by(T308Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t310 ---------------------------------------------------------------------- 
@router.get("/t310_juros/{mes}/{ano}", summary=T310, tags=TAGJDEB)
async def t310_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T310Juros)
                      .filter(extract('year', T310Juros.data) == ano, 
                              extract('month', T310Juros.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t310_juros/periodo", summary=T310, tags=TAGJDEB)
async def t310_juros_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T310Juros,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t310_juros", summary=T310, tags=TAGJDEB)
async def t310_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T310Juros).order_by(T310Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t310 PNN ------------------------------------------------------------------ 
@router.get("/t310_juros_pnn", summary=TPNN, tags=TAGJDEB)
async def t310_juros_pnn(db: Session = Depends(get_db)):
     data_tabela = db.query(T310JurosPnn).order_by(T310JurosPnn.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t312 ---------------------------------------------------------------------- 
@router.get("/t312_selic/{mes}/{ano}", summary=T312, tags=TAGJDEB)
async def t312_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T312Selic)
                      .filter(extract('year', T312Selic.data) == ano, 
                              extract('month', T312Selic.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t312_selic/periodo", summary=T312, tags=TAGJDEB)
async def t312_selic_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T312Selic,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t312_selic", summary=T312, tags=TAGJDEB)
async def t312_selic(db: Session = Depends(get_db)):
     data_tabela = db.query(T312Selic).order_by(T312Selic.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)



# TABELA t314 ---------------------------------------------------------------------- 
@router.get("/t314_juros/{mes}/{ano}", summary=T314, tags=TAGJDEB)
async def t314_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T314Juros)
                      .filter(extract('year', T310Juros.data) == ano, 
                              extract('month', T310Juros.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t314_juros/periodo", summary=T314, tags=TAGJDEB)
async def t314_juros_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T314Juros,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t314_juros", summary=T314, tags=TAGJDEB)
async def t314_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T314Juros).order_by(T314Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t316 ---------------------------------------------------------------------- 
@router.get("/t316_juros/{mes}/{ano}", summary=T316, tags=TAGJDEB)
async def t316_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T316Juros)
                      .filter(extract('year', T316Juros.data) == ano, 
                              extract('month', T316Juros.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t316_juros/periodo", summary=T316, tags=TAGJDEB)
async def t316_juros_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T316Juros,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t316_juros", summary=T316, tags=TAGJDEB)
async def t316_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T316Juros).order_by(T316Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)





# ----------------------------------------------------------------------------------
# TABELAS DE JUROS (320-399) - Créditos
# 322, 324, 326, 328, 330 : Juros | 332, 334: SELIC
# ----------------------------------------------------------------------------------

# TABELA t322 ---------------------------------------------------------------------- 
@router.get("/t322_juros/{mes}/{ano}", summary=T322, tags=TAGJCRE)
async def t322_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T322Juros)
                      .filter(extract('year', T322Juros.data) == ano, 
                              extract('month', T322Juros.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t322_juros/periodo", summary=T322, tags=TAGJCRE)
async def t322_juros_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T322Juros,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t322_juros", summary=T322, tags=TAGJCRE)
async def t322_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T322Juros).order_by(T322Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)



# TABELA t324 -  
@router.get("/t324_juros/{mes}/{ano}", summary=T324, tags=TAGJCRE)
async def t324_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T324Juros)
                      .filter(extract('year', T324Juros.data) == ano, 
                              extract('month', T324Juros.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t324_juros/periodo", summary=T324, tags=TAGJCRE)
async def t324_juros_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T324Juros,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t324_juros", summary=T324, tags=TAGJCRE)
async def t324_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T324Juros).order_by(T324Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)



# TABELA t326 - 
@router.get("/t326_juros/{mes}/{ano}", summary=T326, tags=TAGJCRE)
async def t326_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T326Juros)
                      .filter(extract('year', T326Juros.data) == ano, 
                              extract('month', T326Juros.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t326_juros/periodo", summary=T326, tags=TAGJCRE)
async def t326_juros_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T326Juros,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t326_juros", summary=T326, tags=TAGJCRE)
async def t326_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T326Juros).order_by(T326Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)



# TABELA t328 - 
@router.get("/t328_juros/{mes}/{ano}", summary=T328, tags=TAGJCRE)
async def t328_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T328Juros)
                      .filter(extract('year', T328Juros.data) == ano, 
                              extract('month', T328Juros.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t328_juros/periodo", summary=T328, tags=TAGJCRE)
async def t328_juros_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T328Juros,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t328_juros", summary=T328, tags=TAGJCRE)
async def t328_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T328Juros).order_by(T328Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)



# TABELA t330 - 
@router.get("/t330_juros/{mes}/{ano}", summary=T330, tags=TAGJCRE)
async def t330_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T330Juros)
                      .filter(extract('year', T330Juros.data) == ano, 
                              extract('month', T330Juros.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t330_juros/periodo", summary=T330, tags=TAGJCRE)
async def t330_juros_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T330Juros,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t330_juros", summary=T330, tags=TAGJCRE)
async def t330_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T330Juros).order_by(T330Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t332 - 
@router.get("/t332_selic/{mes}/{ano}", summary=T332, tags=TAGJCRE)
async def t332_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T332Selic)
                      .filter(extract('year', T332Selic.data) == ano, 
                              extract('month', T332Selic.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t332_selic/periodo", summary=T332, tags=TAGJCRE)
async def t332_selic_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T332Selic,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t332_selic", summary=T332, tags=TAGJCRE)
async def t332_selic(db: Session = Depends(get_db)):
     data_tabela = db.query(T332Selic).order_by(T332Selic.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)




# TABELA t334 - 
@router.get("/t334_selic/{mes}/{ano}", summary=T334, tags=TAGJCRE)
async def t334_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T334Selic)
                      .filter(extract('year', T334Selic.data) == ano, 
                              extract('month', T334Selic.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t334_selic/periodo", summary=T334, tags=TAGJCRE)
async def t334_selic_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T334Selic,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t334_selic", summary=T334, tags=TAGJCRE)
async def t334_selic(db: Session = Depends(get_db)):
     data_tabela = db.query(T334Selic).order_by(T334Selic.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)




# TABELA t336 ---------------------------------------------------------------------- 
@router.get("/t336_juros/{mes}/{ano}", summary=T336, tags=TAGJCRE)
async def t336_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T336Juros)
                      .filter(extract('year', T336Juros.data) == ano, 
                              extract('month', T336Juros.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t336_juros/periodo", summary=T336, tags=TAGJCRE)
async def t336_juros_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T336Juros,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t336_juros", summary=T336, tags=TAGJCRE)
async def t336_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T336Juros).order_by(T336Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t338 ---------------------------------------------------------------------- 
@router.get("/t338_juros/{mes}/{ano}", summary=T338, tags=TAGJCRE)
async def t338_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T338Juros)
                      .filter(extract('year', T338Juros.data) == ano, 
                              extract('month', T338Juros.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t338_juros/periodo", summary=T338, tags=TAGJCRE)
async def t338_juros_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T338Juros,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t338_juros", summary=T338, tags=TAGJCRE)
async def t338_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T338Juros).order_by(T338Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)



# TABELA t340 ---------------------------------------------------------------------- 
@router.get("/t340_juros/{mes}/{ano}", summary=T340, tags=TAGJCRE)
async def t340_juros_mes_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T340Juros)
                      .filter(extract('year', T340Juros.data) == ano, 
                              extract('month', T340Juros.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t340_juros/periodo", summary=T340, tags=TAGJCRE)
async def t340_juros_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T340Juros,
                                     mes_inicial,
                                     ano_inicial,
                                     mes_final,
                                     ano_final,
                                     db)

@router.get("/t340_juros", summary=T340, tags=TAGJCRE)
async def t340_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T340Juros).order_by(T340Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)



# -----------------------------------------------------------------------------
# TABELAS DE ÍNDICES PNRJ (400-499) Crédito
# Campos: id, data, indexador, variacao_mensal, numero_indice,
#         fator_vigente, indice_correcao
# -----------------------------------------------------------------------------

# TABELA t400 - 
@router.get("/t400_tabela_pnrj/{mes}/{ano}", summary=T400, tags=TAGCRE)
async def t400_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T400TabelaPnrj)
                      .filter(extract('year', T400TabelaPnrj.data) == ano, 
                              extract('month', T400TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t400_tabela_pnrj/periodo", summary=T400, tags=TAGCRE)
async def t400_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T400TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t400_tabela_pnrj", summary=T400, tags=TAGCRE)
async def t400_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T400TabelaPnrj).order_by(T400TabelaPnrj.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)



# TABELA t402 - 
@router.get("/t402_tabela_pnrj/{mes}/{ano}", summary=T402, tags=TAGCRE)
async def t402_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T402TabelaPnrj)
                      .filter(extract('year', T402TabelaPnrj.data) == ano, 
                              extract('month', T402TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t402_tabela_pnrj/periodo", summary=T402, tags=TAGCRE)
async def t402_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T402TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t402_tabela_pnrj", summary=T402, tags=TAGCRE)
async def t402_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T402TabelaPnrj).order_by(T402TabelaPnrj.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)



# TABELA t404 - 
@router.get("/t404_tabela_pnrj/{mes}/{ano}", summary=T404, tags=TAGCRE)
async def t404_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T404TabelaPnrj)
                      .filter(extract('year', T404TabelaPnrj.data) == ano, 
                              extract('month', T404TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t404_tabela_pnrj/periodo", summary=T404, tags=TAGCRE)
async def t404_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T404TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t404_tabela_pnrj", summary=T404, tags=TAGCRE)
async def t404_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T404TabelaPnrj).order_by(T404TabelaPnrj.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)



# TABELA t406 - 
@router.get("/t406_tabela_pnrj/{mes}/{ano}", summary=T406, tags=TAGCRE)
async def t406_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T406TabelaPnrj)
                      .filter(extract('year', T406TabelaPnrj.data) == ano, 
                              extract('month', T406TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t406_tabela_pnrj/periodo", summary=T406, tags=TAGCRE)
async def t406_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T406TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t406_tabela_pnrj", summary=T406, tags=TAGCRE)
async def t406_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T406TabelaPnrj).order_by(T406TabelaPnrj.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)



# TABELA t408 - 
@router.get("/t408_tabela_pnrj/{mes}/{ano}", summary=T408, tags=TAGCRE)
async def t408_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T408TabelaPnrj)
                      .filter(extract('year', T408TabelaPnrj.data) == ano, 
                              extract('month', T408TabelaPnrj.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t408_tabela_pnrj/periodo", summary=T408, tags=TAGCRE)
async def t408_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T408TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t408_tabela_pnrj", summary=T408, tags=TAGCRE)
async def t408_tabela_pnrj(db: Session = Depends(get_db)):
     data_tabela = db.query(T408TabelaPnrj).order_by(T408TabelaPnrj.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)           



# TABELA t410 ---------------------------------------------------------------------- 
@router.get("/t410_tabela_pnrj/{mes}/{ano}", summary=T410, tags=TAGCRE)
async def t410_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0, lt=13),
                                          ano: int = Path(title="Ano", gt=1900, lt=2100),
                                          db: Session = Depends(get_db)):
    data_tabela = (db.query(T410TabelaPnrj)
                   .filter(extract('year', T410TabelaPnrj.data) == ano,
                           extract('month', T410TabelaPnrj.data) == mes)
                   .first())
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t410_tabela_pnrj/periodo", summary=T410, tags=TAGCRE)
async def t410_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T410TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t410_tabela_pnrj", summary=T410, tags=TAGCRE)
async def t410_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T410TabelaPnrj).all()
    if data_tabela:
        return list(map(formatar_data, data_tabela))
    raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t412 ---------------------------------------------------------------------- 
@router.get("/t412_tabela_pnrj/{mes}/{ano}", summary=T412, tags=TAGCRE)
async def t412_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0, lt=13),
                                          ano: int = Path(title="Ano", gt=1900, lt=2100),
                                          db: Session = Depends(get_db)):
    data_tabela = (db.query(T412TabelaPnrj)
                   .filter(extract('year', T412TabelaPnrj.data) == ano,
                           extract('month', T412TabelaPnrj.data) == mes)
                   .first())
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t412_tabela_pnrj/periodo", summary=T412, tags=TAGCRE)
async def t412_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T412TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t412_tabela_pnrj", summary=T412, tags=TAGCRE)
async def t412_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T412TabelaPnrj).all()
    if data_tabela:
        return list(map(formatar_data, data_tabela))
    raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t414 ---------------------------------------------------------------------- 
@router.get("/t414_tabela_pnrj/{mes}/{ano}", summary=T414, tags=TAGCRE)
async def t414_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0, lt=13),
                                          ano: int = Path(title="Ano", gt=1900, lt=2100),
                                          db: Session = Depends(get_db)):
    data_tabela = (db.query(T414TabelaPnrj)
                   .filter(extract('year', T414TabelaPnrj.data) == ano,
                           extract('month', T414TabelaPnrj.data) == mes)
                   .first())
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t414_tabela_pnrj/periodo", summary=T414, tags=TAGCRE)
async def t414_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T414TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t414_tabela_pnrj", summary=T414, tags=TAGCRE)
async def t414_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T414TabelaPnrj).all()
    if data_tabela:
        return list(map(formatar_data, data_tabela))
    raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t416 ---------------------------------------------------------------------- 
@router.get("/t416_tabela_pnrj/{mes}/{ano}", summary=T416, tags=TAGCRE)
async def t416_tabela_pnrj_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0, lt=13),
                                          ano: int = Path(title="Ano", gt=1900, lt=2100),
                                          db: Session = Depends(get_db)):
    data_tabela = (db.query(T416TabelaPnrj)
                   .filter(extract('year', T416TabelaPnrj.data) == ano,
                           extract('month', T416TabelaPnrj.data) == mes)
                   .first())
    if data_tabela is not None:
        formatar_data(data_tabela)
        return data_tabela
    raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t416_tabela_pnrj/periodo", summary=T416, tags=TAGCRE)
async def t416_tabela_pnrj_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T416TabelaPnrj, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t416_tabela_pnrj", summary=T416, tags=TAGCRE)
async def t416_tabela_pnrj(db: Session = Depends(get_db)):
    data_tabela = db.query(T416TabelaPnrj).all()
    if data_tabela:
        return list(map(formatar_data, data_tabela))
    raise HTTPException(status_code=404, detail=NOREGS)

