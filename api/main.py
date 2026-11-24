from fastapi import FastAPI
from database import engine 
from routers import tabelas
from models import *
from constantes import *

#app = FastAPI()


tags_metadata = [
    {
        "name": METANOME1,
        "description": METADESC1
    },
    {
        "name": METANOME2,
        "description": METADESC2
    },
    {
        "name": METANOME3,
        "description": METADESC3
    },
    {
        "name": METANOME4,
        "description": METADESC4
    },
    {
        "name": METANOME5,
        "description": METADESC5
    },
    {
        "name": METANOME6,
        "description": METADESC6
    }
    
]

app = FastAPI(
    title=TITULO,
    description=DESCRICAO,
    version=VERSAO,
    openapi_tags=tags_metadata
)

# app = FastAPI(
#     title="API Índices - PNRJ",  
#     description="Índices de débitos e créditos, indexadores e juros",
#     version="1.0.0"
# )


Base.metadata.create_all(bind=engine)

app.include_router(tabelas.router)




