# main.py
from database import get_db
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

import backend.database.models as models
from backend.database import database

models.Base.metadata.create_all(bind=database)

app = FastAPI()
