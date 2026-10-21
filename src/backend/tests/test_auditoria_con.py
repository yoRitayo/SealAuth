# Testes da rota do verificador (controllers/auditoria_con.py)
import asyncio

import auditoria
from controle_acesso import ChecadorPermissao
from controllers.auditoria_con import AuditoriaController


def _rota():
    (rota,) = AuditoriaController().router.routes
    return rota


def test_rota_registrada():
    rota = _rota()
    assert rota.path == "/logs-auditoria/verificar"
    assert rota.methods == {"GET"}


def test_rota_exige_permissao_ler_logs():
    checadores = [d.dependency for d in _rota().dependencies if isinstance(d.dependency, ChecadorPermissao)]
    assert [c.permissao for c in checadores] == ["ler_logs"]


def test_verificar_logs_devolve_resultado_do_verificador(monkeypatch):
    recebido = []
    resultado = {"integra": False, "total": 2, "quebra": {"id": 2, "motivo": "hash_divergente"}}

    def verificar_falso(db):
        recebido.append(db)
        return resultado

    monkeypatch.setattr("controllers.auditoria_con.verificar_cadeia", verificar_falso)
    db = object()
    assert asyncio.run(AuditoriaController().verificar_logs(db)) == resultado
    assert recebido == [db]


def test_verificar_logs_usa_o_verificador_real():
    class _DbFalso:
        def scalars(self, consulta):
            return iter([])

    resposta = asyncio.run(AuditoriaController().verificar_logs(_DbFalso()))
    assert resposta == auditoria.verificar_registros([])
