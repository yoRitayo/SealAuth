
import base64
import re

from seguranca import gerar_hash_senha, verificar_senha


# ============================================================
# T01 - A mesma senha gera hashes diferentes (salt único)
# ============================================================

def test_t01_mesma_senha_gera_hashes_diferentes():
    senha = "SenhaFicticia#2026"
    hashes = set()

    for _ in range(1000):
        hash_gerado = gerar_hash_senha(senha)

        assert hash_gerado not in hashes

        hashes.add(hash_gerado)

    assert len(hashes) == 1000


# ============================================================
# T02 - A senha certa passa e variações dela não
# ============================================================

def test_t02_verificacao_de_senha():
    senha = "SenhaFicticia#2026"

    senha_hash = gerar_hash_senha(senha)

    assert verificar_senha(senha_hash, senha) is True

    senhas_incorretas = [
        "senhaFicticia#2026",    # maiúscula trocada
        "SenhaFicticia#2026 ",   # espaço no final
        "SenhaFicticia#2027",    # um caractere diferente
    ]

    for senha_incorreta in senhas_incorretas:
        assert verificar_senha(
            senha_hash, senha_incorreta
        ) is False


# ============================================================
# T03 - Argon2id no formato PHC com parâmetros reconhecidos
#
# Não exige valores exatos: vale qualquer configuração igual ou
# mais forte que algum perfil da RFC 9106 ou da OWASP.
# ============================================================

SENHA_T03 = "SenhaFicticia#2026"

# (memória mínima em KiB, iterações mínimas); paralelismo >= 1 em todos
PERFIS_RECONHECIDOS = {
    "RFC 9106 - recomendacao principal": (2_097_152, 1),
    "RFC 9106 - recomendacao com pouca memoria": (65_536, 3),
    "OWASP - m=47104, t=1": (47_104, 1),
    "OWASP - m=19456, t=2": (19_456, 2),
    "OWASP - m=12288, t=3": (12_288, 3),
    "OWASP - m=9216, t=4": (9_216, 4),
    "OWASP - m=7168, t=5": (7_168, 5),
}

# RFC 9106: salt de 128 bits e tag de 256 bits
TAMANHO_MINIMO_SALT = 16
TAMANHO_MINIMO_TAG = 32

PADRAO_PHC = (
    r"\$argon2id\$v=19\$"
    r"m=(\d+),t=(\d+),p=(\d+)"
    r"\$([A-Za-z0-9+/]+)"
    r"\$([A-Za-z0-9+/]+)"
)


def decodificar_b64(valor):
    # O PHC tira o "=" de preenchimento do base64
    return base64.b64decode(valor + "=" * (-len(valor) % 4))


def separar_hash(senha_hash):
    """Retorna (memória, iterações, paralelismo, salt, tag)."""
    resultado = re.fullmatch(PADRAO_PHC, senha_hash)

    assert resultado is not None, (
        "O hash nao corresponde ao formato PHC Argon2id v=19. "
        f"Hash gerado: {senha_hash}"
    )

    memoria, iteracoes, paralelismo = map(int, resultado.groups()[:3])
    salt = decodificar_b64(resultado.group(4))
    tag = decodificar_b64(resultado.group(5))

    return memoria, iteracoes, paralelismo, salt, tag


# CENÁRIO 1 - Argon2id, versão 19 e formato PHC
def test_t03_formato_phc_argon2id_v19():
    senha_hash = gerar_hash_senha(SENHA_T03)

    separar_hash(senha_hash)

    # O hash no formato certo também precisa funcionar na verificação
    assert verificar_senha(senha_hash, SENHA_T03) is True


# CENÁRIO 2 - Parâmetros atendem pelo menos um perfil
def test_t03_parametros_em_perfil_reconhecido():
    memoria, iteracoes, paralelismo, _, _ = separar_hash(
        gerar_hash_senha(SENHA_T03)
    )

    assert paralelismo >= 1, (
        f"Paralelismo invalido: {paralelismo}."
    )

    atendidos = [
        nome
        for nome, (memoria_min, iteracoes_min) in PERFIS_RECONHECIDOS.items()
        if memoria >= memoria_min and iteracoes >= iteracoes_min
    ]

    assert atendidos, (
        f"Parametros m={memoria} KiB, t={iteracoes}, p={paralelismo} "
        f"abaixo de todos os perfis reconhecidos: {PERFIS_RECONHECIDOS}"
    )


# CENÁRIO 3 - Tamanho mínimo de salt e tag
def test_t03_salt_e_tag_com_tamanho_recomendado():
    _, _, _, salt, tag = separar_hash(gerar_hash_senha(SENHA_T03))

    assert len(salt) >= TAMANHO_MINIMO_SALT, (
        f"Salt de {len(salt)} bytes. "
        f"Minimo: {TAMANHO_MINIMO_SALT} bytes."
    )

    assert len(tag) >= TAMANHO_MINIMO_TAG, (
        f"Tag de {len(tag)} bytes. "
        f"Minimo: {TAMANHO_MINIMO_TAG} bytes."
    )


# CENÁRIO 4 - Salt novo a cada hash
def test_t03_salt_aleatorio():
    _, _, _, salt_1, _ = separar_hash(gerar_hash_senha(SENHA_T03))
    _, _, _, salt_2, _ = separar_hash(gerar_hash_senha(SENHA_T03))

    assert salt_1 != salt_2, (
        "Dois hashes da mesma senha usaram o mesmo salt."
    )
