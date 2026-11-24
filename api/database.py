from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from constantes import *

# postgresql://postgres_user:password@address/database_name
#SQLALCHEMY_DATABASE_URL = "postgresql://postgres:admin@pgsql/indexadores"

# this one is for postgresql
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


#Base = declarative_base()
