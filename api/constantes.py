from decouple import config, Csv

# Dados conexão postgres
SQLALCHEMY_DATABASE_URL = config('SQLALCHEMY_DB_URL')

NOREGS='Não há registro'