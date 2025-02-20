from fastapi import FastAPI
from database import engine 
from routers import tabelas
from models import *

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(tabelas.router)




