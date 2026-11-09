from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from settings import settings
from schema import Base

engine = create_engine(url=settings.DB_URL)
Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = Session() 
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)