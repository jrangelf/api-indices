import json
from sqlalchemy import extract, and_
from sqlalchemy.orm import Session
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
        .all()
    )
    if data_tabela:
        return data_tabela
    
    raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/bcb")
async def indexadores(db: Session = Depends(get_db)):
     s_tr = db.query(Tr).order_by(Tr.id.desc()).first()
     s_selic = db.query(Selic).order_by(Selic.id.desc()).first()
     s_copom = db.query(SelicCopom).order_by(SelicCopom.id.desc()).first()
     s_inpc = db.query(Inpc).order_by(Inpc.id.desc()).first()
     s_ipca = db.query(Ipca).order_by(Ipca.id.desc()).first()
     s_ipca15 = db.query(Ipca15).order_by(Ipca15.id.desc()).first()
     s_igpm = db.query(Igpm).order_by(Igpm.id.desc()).first()
     # Converter a string em um objeto datetime
     #data_hora = datetime.strptime(ls_tr.data, '%Y-%m-%d %H:%M:%S+%z')
     # Formatá-lo como 'dd/mm/yyyy'
     dt_tr = s_tr.data.strftime('%d/%m/%Y')
     dt_selic = s_selic.data.strftime('%d/%m/%Y')
     dt_copom = s_copom.data.strftime('%d/%m/%Y')
     dt_inpc = s_inpc.data.strftime('%d/%m/%Y')
     dt_ipca = s_ipca.data.strftime('%d/%m/%Y')
     dt_ipca15 = s_ipca15.data.strftime('%d/%m/%Y')
     dt_igpm = s_igpm.data.strftime('%d/%m/%Y')
     tr = f"TR: {dt_tr} = {s_tr.valor}"
     selic = f"SELIC: {dt_selic} = {s_selic.valor}"
     selic_copom = f"SELIC COPOM: {dt_copom} = {s_copom.valor}"
     inpc = f"INPC: {dt_inpc} = {s_inpc.valor}"
     ipca = f"IPCA: {dt_ipca} = {s_ipca.valor}"
     ipca15 = f"IPCA-15: {dt_ipca15} = {s_ipca15.valor}"
     igpm = f"IGP-M: {dt_igpm} = {s_igpm.valor}"
     indices = tr,selic,selic_copom,inpc,ipca,ipca15,igpm
     if indices is not None:
         return indices
     raise HTTPException(status_code=404, detail=NOREGS)

@router.get("/descricao_tabelas")
async def descricao_tabelas(db: Session = Depends(get_db)):
     data_tabela = db.query(DescricaoTabelas).all()
     if data_tabela is not None:
         return data_tabela
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

#---------------------------------------------------------------------
#TESTE DE FORMATAÇÃO DE DATAS
#---------------------------------------------------------------------
# Função para serialização personalizada de datas
def custom_json_serializer(obj):
    if isinstance(obj, datetime):
        #return obj.strftime('%Y-%m-%d')  # Formato de data desejado
        return obj.strftime('%d/%m/%Y')
    raise TypeError(f"Type {type(obj)} not serializable")

# Rota de exemplo
@router.get("/exemplo")
async def indexador_ipca(db: Session = Depends(get_db)):
     data_tabela = db.query(Ipca).all()
     if data_tabela is not None:
        data_formatada = [{"data": custom_json_serializer(item.data), "valor": item.valor, "id": item.id} for item in data_tabela]
        return data_formatada
     raise HTTPException(status_code=404, detail=NOREGS)
#----------------------------------------------------------------------



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
     data_tabela = db.query(Ipca).all()
     if data_tabela is not None:
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)

# IPCA-15
@router.get("/ipca15/{mes}/{ano}")
async def buscar_pelo_mes_e_ano(mes: int = Path(title="Mês", gt=0,lt=13),
                                ano: int = Path(title="Ano", gt=1900,lt=2100),
                                db: Session = Depends(get_db)):
       data_tabela = (db.query(Ipca15)
                      .filter(extract('year', Ipca15.data) == ano, extract('month', Ipca15.data) == mes)
                      .first()
                      )
       if data_tabela is not None:
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
     data_tabela = db.query(Ipca15).all()
     if data_tabela is not None:
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
     data_tabela = db.query(Inpc).all()
     if data_tabela is not None:
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
     data_tabela = db.query(Tr).all()
     if data_tabela is not None:
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
     data_tabela = db.query(Selic).all()
     if data_tabela is not None:
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
     data_tabela = db.query(SelicCopom).all()
     if data_tabela is not None:
         return data_tabela
     raise HTTPException(status_code=404, detail=NOREGS)


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
     data_tabela = db.query(T200TabelaPnep).all()
     if data_tabela is not None:
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
               


               