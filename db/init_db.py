from .database import engine
from .models import *
from dotenv import load_dotenv
load_dotenv()
import os

def init_db():
    if os.getenv('ENV') in ('local','test'):
        Base.metadata.create_all(bind=engine)


if __name__=="__main__":
    init_db()