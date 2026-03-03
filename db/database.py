import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

current_path=os.path.dirname(os.path.realpath(__file__))

database_url=os.getenv("DATABASE_URL",f"sqlite:///{current_path}/database.db")

engine=create_engine(database_url,echo=False)

SessionLocal=sessionmaker(bind=engine)

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()