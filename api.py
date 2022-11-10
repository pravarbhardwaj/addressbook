from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from geopy.geocoders import Nominatim
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from math import radians, cos, sin, asin, sqrt

def getDistance(lon1, lat1, lon2, lat2):
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
      
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
 
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in kilometers. Use 3956 for miles
    r = 6371
      
    # calculate the result
    return(c * r)

def checkLocation(latitude, longitude):
    # calling the nominatim tool
    geoLoc = Nominatim(user_agent="GetLoc")
    
    # passing the coordinates
    locname = geoLoc.reverse(f"{longitude}, {latitude}")
    
    # printing the address/location name
    return locname

app = FastAPI()

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


models.Base.metadata.create_all(bind=engine)

class AddressBook(BaseModel):
    address: str
    latitude: float
    longitude: float 

@app.post('/create')
async def create_address(AddressBook:AddressBook, db: Session = Depends(get_db)):
    locName = checkLocation(AddressBook.longitude, AddressBook.latitude)
    if not locName:
        raise HTTPException(status_code=400, detail="Invalid longitude/latitude")
    address_model = models.Addresses()
    address_model.address = AddressBook.address
    address_model.longitude = AddressBook.longitude
    address_model.latitude = AddressBook.latitude
    db.add(address_model)
    db.commit()

    return {**AddressBook.dict()}

@app.get('/')
async def get_data(db: Session = Depends(get_db)):
    return db.query(models.Addresses).all()

@app.put('/update')
async def update_address(address, latitude, longitude, db: Session = Depends(get_db)):
    address_model = db.query(models.Addresses).filter(models.Addresses.address == address).first()
    if address_model is None:
        raise HTTPException(status_code=404, detail="Address does not exist")
    locName = checkLocation(latitude, longitude)
    if not locName:
        raise HTTPException(status_code=400, detail="Invalid longitude/latitude")
    address_model.longitude = longitude
    address_model.latitude = latitude
    db.add(address_model)
    db.commit()
    return {"message": "Successfully updated"}

@app.delete("/delete/{address}")
def delete_address(address: str, db: Session = Depends(get_db)):
    address_model = db.query(models.Addresses).filter(models.Addresses.address == address).first()
    if address_model is None:
        raise HTTPException(status_code=404, detail=f"{address} does not exist")
    db.query(models.Addresses).filter(models.Addresses.address == address).delete()
    db.commit()
    return {"message": f"{address} successfully deleted"}

@app.get('/distance')
def get_addresses(address, distance: float, db: Session = Depends(get_db)):
    address_model = db.query(models.Addresses).filter(models.Addresses.address == address).first()
    if address_model is None:
        raise HTTPException(status_code=404, detail=f"{address} does not exist")
    all_addresses = db.query(models.Addresses).all()
    address_list = list()
    for add in all_addresses:
        if add.address == address_model.address:
            continue
        dist = getDistance(address_model.longitude, address_model.latitude, add.longitude, add.latitude)
        if dist <= distance:
            address_list.append(add)
    return address_list