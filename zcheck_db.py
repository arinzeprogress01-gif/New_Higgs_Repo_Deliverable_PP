from app.database import SessionLocal
from app import models

db = SessionLocal()

users = db.query(models.User).all()

for user in users:
    print(user.id, user.email, user.password)
