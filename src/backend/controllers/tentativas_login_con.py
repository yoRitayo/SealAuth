
from fastapi import APIRouter


class TentativasLoginController:
    def __init__(self):
        self.router = APIRouter(tags=["tentativas_login"])
