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