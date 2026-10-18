# main.py
from controllers.alertas_con import AlertasController
from controllers.auth_con import AuthController
from controllers.bloqueios_ip_con import BloqueiosIPController
from controllers.logs_auditoria_con import LogsAuditoriaController
from controllers.tentativas_login_con import TentativasLoginController
from controllers.usuarios_con import UsuariosController
from database.database import Base, engine
from fastapi import FastAPI

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(AuthController().router)
app.include_router(UsuariosController().router)
app.include_router(LogsAuditoriaController().router)
app.include_router(AlertasController().router)
app.include_router(BloqueiosIPController().router)
app.include_router(TentativasLoginController().router)
