from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base

# create engine
engine = create_engine('sqlite:///game.db')

# create base class
Base = declarative_base()

# create user table
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    dino_x = Column(Integer)
    dino_y = Column(Integer)
    jumping = Column(Integer)
    seconds = Column(Integer)
    bad_cord = Column(Integer)
    bad_cord2 = Column(Integer)
    score = Column(Integer)

# create tables
Base.metadata.create_all(engine)