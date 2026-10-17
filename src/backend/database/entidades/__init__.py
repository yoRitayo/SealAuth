from database.entidades.alertas_ent import Alerta
from database.entidades.bloqueio_ip_ent import BloqueioIP
from database.entidades.logs_auditoria_ent import LogAuditoria
from database.entidades.tentativas_login_ent import TentativaLogin
from database.entidades.usuarios_ent import Usuario

# Importar o pacote registra todas as entidades no metadata do Base.
__all__ = ["Alerta", "BloqueioIP", "LogAuditoria", "TentativaLogin", "Usuario"]
