from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

engine = create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}", echo=True)

Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()
