# Política de senha aplicada no servidor: mesma regra e mensagens do ValidadorDeSenha
# do frontend (src/frontend/pages/utils.ts). Se a regra mudar lá, precisa mudar aqui.
import re
from typing import Annotated

from pydantic import AfterValidator
from pydantic_core import PydanticCustomError

SENHAS_IMPEDIDAS = frozenset(
    {
        "12345678", "123456789", "1234567890", "00000000", "11111111", "87654321",
        "qwertyuiop", "asdfghjkl", "zxcvbnm1", "qwerty1234", "qwertyui",
        "password", "password123", "administrator", "password1", "welcome1",
        "iloveyou", "sunshine", "princess", "football", "superman",
        "senha123", "senha1234", "mudar123", "mudar1234", "administrador",
        "usuario123", "bemvindo", "bemvindo123", "deusereirei", "brasil123",
        "admin123",
    }
)

TAMANHO_MAXIMO = 64
# Minúscula, maiúscula, dígito, símbolo e no mínimo 8 caracteres ([0-9] igual ao \d do JavaScript)
_FORMATO = re.compile(r"(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{8,}")
# Mesmo caractere 4 vezes seguidas ou mais
_REPETIDOS = re.compile(r"(.)\1{3,}")


def _recusar(mensagem: str) -> None:
    # PydanticCustomError: o 422 sai só com a mensagem, sem o prefixo "Value error,"
    raise PydanticCustomError("senha_fraca", mensagem)


def validar_senha(senha: str) -> str:
    if len(senha) > TAMANHO_MAXIMO:
        _recusar("A senha não deve exceder 64 caracteres.")
    if _REPETIDOS.search(senha):
        _recusar("A senha não pode conter caracteres idênticos repetidos consecutivamente.")
    if not _FORMATO.fullmatch(senha):
        _recusar(
            "A senha deve ter no mínimo 8 caracteres, com letras maiúscula/minúscula, "
            "1 dígito e ao menos um símbolo especial"
        )
    if senha.lower().strip() in SENHAS_IMPEDIDAS:
        _recusar("Esta senha é muito comum ou foi vazada. Escolha outra.")
    return senha


# Usado nos campos de senha nova (cadastro, alteração e redefinição); o login não valida
SenhaForte = Annotated[str, AfterValidator(validar_senha)]
