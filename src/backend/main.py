# main.py
import auditoria  # registra os listeners do log de auditoria
from controllers.alertas_con import AlertasController
from controllers.auditoria_con import AuditoriaController
from controllers.auth_con import AuthController
from controllers.bloqueios_ip_con import BloqueiosIPController
from controllers.logs_auditoria_con import LogsAuditoriaController
from controllers.tentativas_login_con import TentativasLoginController
from controllers.usuarios_con import UsuariosController
import os
from pathlib import Path

from config import FRONTEND_URL
from database.database import Base, engine_admin
from deteccao import verificar_firewall
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

PROTECOES_SQL = Path(__file__).parent / "database" / "protecoes.sql"
APP_USUARIO = os.getenv("BANCO_APP_USUARIO", "seal_app")


def preparar_banco() -> None:
    # Tabelas são criadas pelo admin, então o app (restrito) não é dono delas
    Base.metadata.create_all(bind=engine_admin)
    usuario_quotado = '"' + APP_USUARIO.replace('"', '""') + '"'
    sql = PROTECOES_SQL.read_text(encoding="utf-8").replace(
        "__APP_USUARIO__", usuario_quotado
    )
    with engine_admin.begin() as conexao:
        conexao.exec_driver_sql(sql)


preparar_banco()

app = FastAPI(
    title="SealAuth API",
    version="0.1.0",
    description=(
        "Para testar rotas protegidas: faça login em /auth/login pelo botão **Authorize** "
        "(usuário e senha). O refresh token fica em cookie HttpOnly e não aparece na resposta."
    ),
    # Firewall: IP em BLOQUEIOS_IP recebe 403 antes de qualquer rota (dentro do CORS)
    dependencies=[Depends(verificar_firewall)],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,  # necessário para o cookie do refresh token
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def registrar_ip(requisicao: Request, chamar_proximo):
    # IP de origem usado no log de auditoria
    auditoria.ip_requisicao.set(requisicao.client.host if requisicao.client else None)
    return await chamar_proximo(requisicao)


app.include_router(AuthController().router)
app.include_router(UsuariosController().router)
app.include_router(AuditoriaController().router)
app.include_router(LogsAuditoriaController().router)
app.include_router(AlertasController().router)
app.include_router(BloqueiosIPController().router)
app.include_router(TentativasLoginController().router)
