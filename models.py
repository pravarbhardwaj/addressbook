from sqlalchemy import Column, Integer, String, Float
from database import Base

class Addresses(Base):
    __tablename__ = "addressbook"

    address = Column(String, primary_key=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)

