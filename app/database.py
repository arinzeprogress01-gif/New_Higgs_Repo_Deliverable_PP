from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

#sql Database file path, creates database and setups into the file chuks_kitchen.db

DATABASE_URL = "sqlite:///./chuks_database.db"

#creates engine( links the python to the database)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread":False} #disabale same thread restrictions of the database

)


#This is how we talk to the database,Every API request will:Open session,Query database,Commit changes and Close session
SessionLocal = sessionmaker(

    autocommit=False,#disabale autocommit

    autoflush=False,#disable autoflush
    
    bind=engine
)

#Base class for models
Base = declarative_base()

#get_db function
def get_db():
    db = SessionLocal()  # open session
    try:
        yield db  # yield the session
    finally:
        db.close()  # always close session