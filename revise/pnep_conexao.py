import psycopg2
#from psycopg2 import sql

from bt_constantes import *

def conectar_db():
    conn = None
    try:
        conn = psycopg2.connect(host=HOST, 
                                dbname=DBNAME, 
                                user=USER, 
                                password=PASSWORD,
                                port=PORT)        
    except Exception as e:
        print(f"Erro: {e}")

    return conn
        
