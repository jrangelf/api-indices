from decouple import config, Csv

# Dados conexão postgres
SQLALCHEMY_DATABASE_URL = config('SQLALCHEMY_DB_URL')

HOST = config('HOST')
DBNAME = config('DBNAME')
USER = config('USER')
PASSWORD = config('PASSWORD')
PORT = config('PORT')

SELIC = config('SELIC')
INPC = config('INPC')
IPCA = config('IPCA')
IPCA15 = config('IPCA15')
SELICCOPOM = config('SELICCOPOM')
TR = config('TR')

