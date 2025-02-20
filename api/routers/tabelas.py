import json
from sqlalchemy import extract, and_
from sqlalchemy.orm import Session
from sqlalchemy import desc
from starlette import status
from fastapi import APIRouter, Depends, HTTPException, Path, status, Query, Body
from database import SessionLocal, engine
from models import *
from datetime import datetime

from tools import *
from constantes import NOREGS

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Base.metadata.create_all(bind=engine)

def formatar_data(item):
    item.data = item.data.strftime("%d/%m/%Y")
    return item

def validar_busca_por_periodo(model, mes_inicial, ano_inicial, mes_final, ano_final, db):
    if ano_inicial > ano_final or (ano_inicial == ano_final and mes_inicial > mes_final):
        raise HTTPException(status_code=400, detail="Período inválido: mês/ano inicial é maior que mês/ano final")

    data_tabela = (
        db.query(model)
        .filter(
            and_(
                extract('year', model.data) >= ano_inicial,
                extract('month', model.data) >= mes_inicial
            ),
            and_(
                extract('year', model.data) <= ano_final,
                extract('month', model.data) <= mes_final
            )
        )
        .order_by(model.data)
        .all()
    )
    if data_tabela:
        data_tabela = list(map(formatar_data, data_tabela))
        return data_tabela
    
    raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/bcb")
async def indexadores(db: Session = Depends(get_db)):
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


@router.get("/descricao_tabelas")
async def descricao_tabelas(db: Session = Depends(get_db)):
     data_tabela = db.query(DescricaoTabelas).order_by(DescricaoTabelas.codigo).all()
     if data_tabela is not None:
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


@router.get("/nome_tabelas")
async def nome_e_codigo_das_tabelas(db: Session = Depends(get_db)):
     #data_tabela = db.query(DescricaoTabelas).order_by(DescricaoTabelas.codigo).all()
     data_tabela = db.query(
        DescricaoTabelas.codigo,
        DescricaoTabelas.nome,
        DescricaoTabelas.descricao,
        DescricaoTabelas.observacao
    ).order_by(DescricaoTabelas.codigo).all()
     
     if data_tabela is not None:
         return [
        {
            "codigo": row.codigo,
            "nome": row.nome,
            "descricao": row.descricao,
            "observacao": row.observacao
        } 
        for row in data_tabela
        ]
     raise HTTPException(status_code=404, detail=NOREGS)


@router.get("/indexadores")
async def indexadores_bc(db: Session = Depends(get_db)):
     data_tabela = db.query(Indexadores).all()
     if data_tabela is not None:
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/logatualizacao")
async def log_atualizacao(db: Session = Depends(get_db)):
     data_tabela = db.query(LogAtualizacao).all()
     if data_tabela is not None:
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)

# #---------------------------------------------------------------------
# #TESTE DE FORMATAÇÃO DE DATAS
# #---------------------------------------------------------------------
# # Função para serialização personalizada de datas
# def custom_json_serializer(obj):
#     if isinstance(obj, datetime):
#         #return obj.strftime('%Y-%m-%d')  # Formato de data desejado
#         return obj.strftime('%d/%m/%Y')
#     raise TypeError(f"Type {type(obj)} not serializable")

# # Rota de exemplo
# @router.get("/exemplo")
# async def indexador_ipca(db: Session = Depends(get_db)):
#      data_tabela = db.query(Ipca).all()
#      if data_tabela is not None:
#         data_formatada = [{"data": custom_json_serializer(item.data), "valor": item.valor, "id": item.id} for item in data_tabela]
#         return data_formatada
#      raise HTTPException(status_code=404, detail=NOREGS)
# #----------------------------------------------------------------------
# listar em ordem decrescente: data_tabela = db.query(Ipca).order_by(desc(Ipca.data)).all() 

# *** TABELA DE INDEXADORES DO BANCO CENTRAL ***

# IPCA
@router.get("/ipca/{mes}/{ano}")
async def buscar_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(Ipca)
                      .filter(extract('year', Ipca.data) == ano, extract('month', Ipca.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/ipca/periodo")
async def buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)):

    return validar_busca_por_periodo(Ipca, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/ipca")
async def indexador_ipca(db: Session = Depends(get_db)):
     data_tabela = db.query(Ipca).order_by(Ipca.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)

# IPCA-15
@router.get("/ipca15/{mes}/{ano}")
async def buscar_pelo_mes_e_ano(
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

@router.get("/ipca15/periodo")
async def buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)):

    return validar_busca_por_periodo(Ipca15, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/ipca15")
async def indexador_ipca15(db: Session = Depends(get_db)):
     data_tabela = db.query(Ipca15).order_by(Ipca15.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)

# INPC
@router.get("/inpc/{mes}/{ano}")
async def buscar_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
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

@router.get("/inpc/periodo")
async def buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(Inpc, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/inpc")
async def indexador_inpc(db: Session = Depends(get_db)):
     data_tabela = db.query(Inpc).order_by(Inpc.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TR
@router.get("/tr/{mes}/{ano}")
async def buscar_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
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


@router.get("/tr/periodo")
async def buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(Tr, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/tr")
async def indexador_tr(db: Session = Depends(get_db)):
     data_tabela = db.query(Tr).order_by(Tr.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# SELIC
@router.get("/selic/{mes}/{ano}")
async def buscar_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
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

@router.get("/selic/periodo")
async def buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(Selic, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/selic")
async def indexador_selic(db: Session = Depends(get_db)):
     data_tabela = db.query(Selic).order_by(Selic.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# SELIC COPOM
@router.get("/seliccopom/{mes}/{ano}")
async def buscar_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
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

@router.get("/seliccopom/periodo")
async def buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(SelicCopom, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/seliccopom")
async def indexador_selic_copom(db: Session = Depends(get_db)):
     data_tabela = db.query(SelicCopom).order_by(SelicCopom.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# IGPM
@router.get("/igpm/{mes}/{ano}")
async def buscar_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
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

@router.get("/igpm/periodo")
async def buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)):

    return validar_busca_por_periodo(Igpm, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/igpm")
async def indexador_ipca(db: Session = Depends(get_db)):
     data_tabela = db.query(Igpm).order_by(Igpm.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# *** TABELAS DE INDICES PNEP ***

# TABELA t200 - 
@router.get("/t200_tabela_pnep/{mes}/{ano}")
async def t200_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T200TabelaPnep)
                      .filter(extract('year', T200TabelaPnep.data) == ano, 
                              extract('month', T200TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t200_tabela_pnep/periodo")
async def t200_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T200TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t200_tabela_pnep")
async def t200_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T200TabelaPnep).order_by(T200TabelaPnep.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t202 -
@router.get("/t202_tabela_pnep/{mes}/{ano}")
async def t202_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T202TabelaPnep)
                      .filter(extract('year', T202TabelaPnep.data) == ano, 
                              extract('month', T202TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t202_tabela_pnep/periodo")
async def t202_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)):

    return validar_busca_por_periodo(T202TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t202_tabela_pnep")
async def t202_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T202TabelaPnep).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t204 - 
@router.get("/t204_tabela_pnep/{mes}/{ano}")
async def t204_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T204TabelaPnep)
                      .filter(extract('year', T204TabelaPnep.data) == ano, 
                              extract('month', T204TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t204_tabela_pnep/periodo")
async def t204_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T204TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t204_tabela_pnep")
async def t204_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T204TabelaPnep).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t206 - 
@router.get("/t206_tabela_pnep/{mes}/{ano}")
async def t206_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T206TabelaPnep)
                      .filter(extract('year', T206TabelaPnep.data) == ano, 
                              extract('month', T206TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t206_tabela_pnep/periodo")
async def t206_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T206TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t206_tabela_pnep")
async def t206_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T206TabelaPnep).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t208 - 
@router.get("/t208_tabela_pnep/{mes}/{ano}")
async def t208_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T208TabelaPnep)
                      .filter(extract('year', T208TabelaPnep.data) == ano, 
                              extract('month', T208TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t208_tabela_pnep/periodo")
async def t206_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T208TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t208_tabela_pnep")
async def t208_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T208TabelaPnep).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t210 - 
@router.get("/t210_tabela_pnep/{mes}/{ano}")
async def t210_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T210TabelaPnep)
                      .filter(extract('year', T210TabelaPnep.data) == ano, 
                              extract('month', T210TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t210_tabela_pnep/periodo")
async def t206_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T210TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t210_tabela_pnep")
async def t210_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T210TabelaPnep).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)
					

# TABELA t212 - 
@router.get("/t212_tabela_pnep/{mes}/{ano}")
async def t212_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T212TabelaPnep)
                      .filter(extract('year', T212TabelaPnep.data) == ano, 
                              extract('month', T212TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t212_tabela_pnep/periodo")
async def t212_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T212TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t212_tabela_pnep")
async def t212_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T212TabelaPnep).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t214 - 
@router.get("/t214_tabela_pnep/{mes}/{ano}")
async def t214_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T214TabelaPnep)
                      .filter(extract('year', T214TabelaPnep.data) == ano, 
                              extract('month', T214TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t214_tabela_pnep/periodo")
async def t214_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T214TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t214_tabela_pnep")
async def t214_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T214TabelaPnep).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t216 - 
@router.get("/t216_tabela_pnep/{mes}/{ano}")
async def t216_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T216TabelaPnep)
                      .filter(extract('year', T216TabelaPnep.data) == ano, 
                              extract('month', T216TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t216_tabela_pnep/periodo")
async def t216_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T216TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t216_tabela_pnep")
async def t216_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T216TabelaPnep).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t218 - 
@router.get("/t218_tabela_pnep/{mes}/{ano}")
async def t218_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T218TabelaPnep)
                      .filter(extract('year', T218TabelaPnep.data) == ano, 
                              extract('month', T218TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t218_tabela_pnep/periodo")
async def t218_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T218TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t218_tabela_pnep")
async def t218_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T218TabelaPnep).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t220 - 
@router.get("/t220_tabela_pnep/{mes}/{ano}")
async def t220_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T220TabelaPnep)
                      .filter(extract('year', T220TabelaPnep.data) == ano, 
                              extract('month', T220TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t220_tabela_pnep/periodo")
async def t220_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T220TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t220_tabela_pnep")
async def t220_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T220TabelaPnep).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t222 - 
@router.get("/t222_tabela_pnep/{mes}/{ano}")
async def t222_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T222TabelaPnep)
                      .filter(extract('year', T222TabelaPnep.data) == ano, 
                              extract('month', T222TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t222_tabela_pnep/periodo")
async def t222_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T222TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t222_tabela_pnep")
async def t222_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T222TabelaPnep).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t224 - 
@router.get("/t224_tabela_pnep/{mes}/{ano}")
async def t224_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T224TabelaPnep)
                      .filter(extract('year', T224TabelaPnep.data) == ano, 
                              extract('month', T224TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t224_tabela_pnep/periodo")
async def t224_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T224TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t224_tabela_pnep")
async def t224_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T224TabelaPnep).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t226 - 
@router.get("/t226_tabela_pnep/{mes}/{ano}")
async def t226_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T226TabelaPnep)
                      .filter(extract('year', T226TabelaPnep.data) == ano, 
                              extract('month', T226TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t226_tabela_pnep/periodo")
async def t226_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T226TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t226_tabela_pnep")
async def t226_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T226TabelaPnep).order_by(T226TabelaPnep.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t228 - 
@router.get("/t228_tabela_pnep/{mes}/{ano}")
async def t228_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T228TabelaPnep)
                      .filter(extract('year', T228TabelaPnep.data) == ano, 
                              extract('month', T228TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t228_tabela_pnep/periodo")
async def t228_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T228TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t228_tabela_pnep")
async def t228_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T228TabelaPnep).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t230 - 
@router.get("/t230_tabela_pnep/{mes}/{ano}")
async def t230_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T230TabelaPnep)
                      .filter(extract('year', T230TabelaPnep.data) == ano, 
                              extract('month', T230TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t230_tabela_pnep/periodo")
async def t230_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T230TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t230_tabela_pnep")
async def t230_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T230TabelaPnep).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)

# TABELA t232 - 
@router.get("/t232_tabela_pnep/{mes}/{ano}")
async def t232_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T232TabelaPnep)
                      .filter(extract('year', T232TabelaPnep.data) == ano, 
                              extract('month', T232TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t232_tabela_pnep/periodo")
async def t232_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T232TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t232_tabela_pnep")
async def t232_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T232TabelaPnep).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)

# TABELA t234 - 
@router.get("/t234_tabela_pnep/{mes}/{ano}")
async def t234_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T234TabelaPnep)
                      .filter(extract('year', T234TabelaPnep.data) == ano, 
                              extract('month', T234TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t234_tabela_pnep/periodo")
async def t234_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T234TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t234_tabela_pnep")
async def t234_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T234TabelaPnep).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)



# TABELA t236 - 
@router.get("/t236_tabela_pnep/{mes}/{ano}")
async def t236_tabela_pnep_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(T236TabelaPnep)
                      .filter(extract('year', T236TabelaPnep.data) == ano, 
                              extract('month', T236TabelaPnep.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
            formatar_data(data_tabela)
            return data_tabela
       raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/t236_tabela_pnep/periodo")
async def t236_tabela_pnep_buscar_por_periodo(
    mes_inicial: int = Query(..., title="Mês inicial", gt=0, lt=13),
    ano_inicial: int = Query(..., title="Ano inicial", gt=1900, lt=2100),
    mes_final: int = Query(..., title="Mês final", gt=0, lt=13),
    ano_final: int = Query(..., title="Ano final", gt=1900, lt=2100),
    db: Session = Depends(get_db)
):
    return validar_busca_por_periodo(T236TabelaPnep, mes_inicial, ano_inicial, mes_final, ano_final, db)

@router.get("/t236_tabela_pnep")
async def t236_tabela_pnep(db: Session = Depends(get_db)):
     data_tabela = db.query(T236TabelaPnep).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)



# *** TABELAS DE JUROS ***

# TABELA t300 - 
@router.get("/t300_juros_poupanca/{mes}/{ano}")
async def t300_juros_poupanca(mes: int = Path(title="Mês", gt=0,lt=13),
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

@router.get("/t300_juros_poupanca/periodo")
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

@router.get("/t300_juros_poupanca")
async def t300_juros_poupanca(db: Session = Depends(get_db)):
     data_tabela = db.query(T300Juros).order_by(T300Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t302 - 
@router.get("/t302_juros/{mes}/{ano}")
async def t302_juros(mes: int = Path(title="Mês", gt=0,lt=13),
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

@router.get("/t302_juros/periodo")
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

@router.get("/t302_juros")
async def t302_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T302Juros).order_by(T302Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t304 - 
@router.get("/t304_juros/{mes}/{ano}")
async def t304_juros(mes: int = Path(title="Mês", gt=0,lt=13),
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

@router.get("/t304_juros/periodo")
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

@router.get("/t304_juros")
async def t304_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T304Juros).order_by(T304Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t306 - 
@router.get("/t306_juros/{mes}/{ano}")
async def t306_juros(mes: int = Path(title="Mês", gt=0,lt=13),
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

@router.get("/t306_juros/periodo")
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

@router.get("/t306_juros")
async def t306_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T306Juros).order_by(T306Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t308 - 
@router.get("/t308_juros/{mes}/{ano}")
async def t308_juros(mes: int = Path(title="Mês", gt=0,lt=13),
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

@router.get("/t308_juros/periodo")
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

@router.get("/t308_juros")
async def t308_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T308Juros).order_by(T308Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t310 - 
@router.get("/t310_juros/{mes}/{ano}")
async def t310_juros(mes: int = Path(title="Mês", gt=0,lt=13),
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

@router.get("/t310_juros/periodo")
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

@router.get("/t310_juros")
async def t310_juros(db: Session = Depends(get_db)):
     data_tabela = db.query(T310Juros).order_by(T310Juros.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# TABELA t312 - 
@router.get("/t312_selic/{mes}/{ano}")
async def t312_juros(mes: int = Path(title="Mês", gt=0,lt=13),
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

@router.get("/t312_selic/periodo")
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

@router.get("/t312_selic")
async def t312_selic(db: Session = Depends(get_db)):
     data_tabela = db.query(T312Selic).order_by(T312Selic.data).all()
     if data_tabela is not None:
         data_tabela = list(map(formatar_data, data_tabela))
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


# @router.get("/inventario")
# async def inventario(db: Session = Depends(get_db)):
#     data_tabela = db.query(C01tabelainventario).all()
#     if data_tabela is not None:
#         return data_tabela
#     raise HTTPException(status_code=404, detail=NOREGS)

"""
@router.get("/inventario/")
async def busca_obs_pelo_codigo_tabela(codigo_tabela: int = Path(gt=0,lt=30),
                        db: Session = Depends(get_db)):
        
        data_tabela = db.query(C01tabelainventario.C01_NOME_TABELA,C01tabelainventario.C01_OBS_TABELA).filter(C01tabelainventario.C01_CODIGO == codigo_tabela).first()
        if data_tabela is not None:
            return data_tabela
        raise HTTPException(status_code=404, detail=NOREGS)
"""
    

# @router.get("/codigo_tabela/{nome_tabela}")
# async def busca_codigo_tabela_pelo_titulo(nome_tabela: str,
#                         db: Session = Depends(get_db)):
#         data = db.query(C01tabelainventario).filter(C01tabelainventario.C01_NOME_TABELA == nome_tabela).first()
#         if data is not None:
#             return data
#         raise HTTPException(status_code=404, detail=NOREGS)


# @router.get("/tabela/{tabela_cod}")
# async def busca_tabela_pelo_codigo_tabela(tabela_cod: int = Path(gt=0,lt=30),
#                         db: Session = Depends(get_db)):
#         tabela = ajusta_nome_tabela(tabela_cod)
        
#         data_tabela = db.query(eval(tabela)).all()
#         if data_tabela is not None:
#             return data_tabela
#         raise HTTPException(status_code=404, detail=NOREGS)



"""
from sqlalchemy import create_engine
 
engine = create_engine('sqlite:///:memory:')
result = engine.execute("SELECT * FROM users WHERE age >= :age", {'age': 21})
for row in result:
    print(row)


from sqlalchemy.orm import Session
 
session = Session(bind=engine)
result = session.execute("SELECT * FROM users WHERE age >= :age", {'age': 21})
for row in result:
    print(row)

"""
               


               