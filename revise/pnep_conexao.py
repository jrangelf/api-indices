import psycopg2
from pnep_constantes import *

class Singleton(type):

    __instances = {}

    def __call__(cls, *args, **kwargs):

        if cls not in cls.__instances:
            cls.__instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.__instances[cls]
    

class Database(metaclass=Singleton):
    
    conn = None     

    def conectar(self):
        if self.conn is None:
            #print('estabelecendo conexao com o banco de dados')
            try:
                conn = psycopg2.connect(host=HOST, 
                                    dbname=DBNAME, 
                                    user=USER, 
                                    password=PASSWORD,
                                    port=PORT)        
            except Exception as e:
                print(f"Erro: {e}")

        return conn