from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel): 
    email: EmailStr
    phone: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class VerifyUser(BaseModel):
    email: EmailStr
    otp: str

class GetUser(BaseModel):
    id: int
    email: EmailStr
    phone: str

class FoodCreate(BaseModel):
    name: str
    description: str
    price: float

class FoodResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    is_available: bool

class Config:
        orm_mode = True

class cartAdd(BaseModel):
    user_id: int
    food_id: int
    quantity: int

#class getCart(BaseModel):

#FastAPI receives JSON 
#JSON → dictionary
#Dictionary → validated
#Validated → Pydantic object

#That object is passed to your route function.👉 Data transformation layer

"""Flow looks like this:

Frontend JSON
→ Pydantic validation
→ Pydantic object
→ model_dump()
→ SQLAlchemy model
→ Database """