from fastapi import FastAPI

from .database import engine
from . import models
from app.routes import auth


models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth.router)

@app.get("/")
def start_up_info():
    return("chuks_kitchen server is running")
