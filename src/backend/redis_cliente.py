# Redis: rate limiting (janela deslizante) e sessões de refresh token.
# O Redis guarda só o SHA-256 do refresh token, nunca o token em claro.
import time
import uuid

import redis
from config import (
    ATIVACAO_TOKEN_TTL_HORAS,
    REDEFINICAO_TOKEN_TTL_MINUTOS,
    REDIS_URL,
    REFRESH_TOKEN_EXPIRAMENTO_DIAS,
)
from seguranca import gerar_refresh_token, hash_refresh_token

# ------- REFRESH TOKENS -------------
cliente = redis.Redis.from_url(REDIS_URL, decode_responses=True)

TTL_REFRESH_SEGUNDOS = REFRESH_TOKEN_EXPIRAMENTO_DIAS * 24 * 60 * 60

# Atômico: impede que duas renovações simultâneas usem o mesmo token.
# Retorna {estado, familia, usuario_id}; estado: ok | reuso | revogada | inexistente

_ROTACIONAR = cliente.register_script("""local estado = redis.call('HGET', KEYS[1], 'estado')

                                        if not estado then return {'inexistente', '', ''} end

                                        local familia = redis.call('HGET', KEYS[1], 'familia')

                                        local usuario_id = redis.call('HGET', KEYS[1], 'usuario_id')

                                        local chave_revogada = 'familia_revogada:' .. familia

                                        if redis.call('EXISTS', chave_revogada) == 1 then
                                        return {'revogada', familia, usuario_id}
                                        end

                                        if estado == 'usado' then
                                        -- token já usado foi reapresentado: indício de roubo, revoga a família inteira
                                        redis.call('SET', chave_revogada, '1', 'EX', ARGV[1])
                                        return {'reuso', familia, usuario_id}

                                        end
                                        redis.call('HSET', KEYS[1], 'estado', 'usado')
                                        return {'ok', familia, usuario_id}
                                        """)


def _texto(valor: bytes | str) -> str:
    # Com decode_responses=True o valor já é str; o tipo do redis-py ainda admite bytes
    return valor.decode() if isinstance(valor, bytes) else valor


def verificar_rate_limit(chave: str, limite: int, janela: int) -> bool:
    # conta as tentativas dos últimos segundos.
    # Retorna True se a requisição ainda está dentro do limite.
    agora = time.time()
    pipeline = cliente.pipeline()
    pipeline.zremrangebyscore(chave, 0, agora - janela)
    pipeline.zadd(chave, {f"{agora}:{uuid.uuid4()}": agora})
    pipeline.zcard(chave)
    pipeline.expire(chave, janela)
    _, _, quantidade, _ = pipeline.execute()
    return quantidade <= limite


def criar_sessao(usuario_id: uuid.UUID | str, familia: str) -> str:
    # Gera um refresh token novo, guarda o hash no Redis e devolve o token em claro
    token = gerar_refresh_token()
    chave = f"refresh:{hash_refresh_token(token)}"
    pipeline = cliente.pipeline()
    pipeline.hset(
        chave,
        mapping={
            "usuario_id": str(usuario_id),
            "familia": familia,
            "estado": "ativo",
        },
    )
    pipeline.expire(chave, TTL_REFRESH_SEGUNDOS)
    pipeline.sadd(f"usuario_familias:{usuario_id}", familia)
    pipeline.expire(f"usuario_familias:{usuario_id}", TTL_REFRESH_SEGUNDOS)
    pipeline.execute()
    return token


def rotacionar_sessao(token: str) -> tuple[str, str, str, str | None]:
    # Retorna (estado, familia, usuario_id, novo_token); novo_token só existe se estado == "ok"
    resultado = _ROTACIONAR(
        keys=[f"refresh:{hash_refresh_token(token)}"], args=[TTL_REFRESH_SEGUNDOS]
    )
    estado, familia, usuario_id = resultado
    if estado != "ok":
        return estado, familia, usuario_id, None
    novo_token = criar_sessao(usuario_id, familia)
    return estado, familia, usuario_id, novo_token


def revogar_familia(familia: str) -> None:
    cliente.set(f"familia_revogada:{familia}", "1", ex=TTL_REFRESH_SEGUNDOS)


def revogar_sessao(token: str) -> None:
    # Logout: revoga a família à qual o token pertence
    familia = cliente.hget(f"refresh:{hash_refresh_token(token)}", "familia")
    if familia:
        revogar_familia(_texto(familia))


def revogar_todas_sessoes(usuario_id: uuid.UUID | str) -> None:
    # Troca de senha, bloqueio ou exclusão
    for familia in cliente.smembers(f"usuario_familias:{usuario_id}"):
        revogar_familia(_texto(familia))


# ------- TOKENS DE ATIVAÇÃO E REDEFINIÇÃO DE SENHA -------------
# São de uso único: a leitura (GETDEL) já consome e invalida o token.


def _criar_token_uso_unico(
    prefixo: str, usuario_id: "uuid.UUID | str", ttl_segundos: int
) -> str:
    token = gerar_refresh_token()  # mesma geração de 256 bits, reaproveitada
    cliente.set(
        f"{prefixo}:{hash_refresh_token(token)}", str(usuario_id), ex=ttl_segundos
    )
    return token


def _consumir_token_uso_unico(prefixo: str, token: str) -> str | None:
    valor = cliente.getdel(f"{prefixo}:{hash_refresh_token(token)}")
    return _texto(valor) if valor else None


def criar_token_ativacao(usuario_id: "uuid.UUID | str") -> str:
    return _criar_token_uso_unico(
        "ativacao", usuario_id, ATIVACAO_TOKEN_TTL_HORAS * 60 * 60
    )


def consumir_token_ativacao(token: str) -> str | None:
    return _consumir_token_uso_unico("ativacao", token)


def criar_token_redefinicao(usuario_id: "uuid.UUID | str") -> str:
    return _criar_token_uso_unico(
        "redefinicao", usuario_id, REDEFINICAO_TOKEN_TTL_MINUTOS * 60
    )


def consumir_token_redefinicao(token: str) -> str | None:
    return _consumir_token_uso_unico("redefinicao", token)
