# Respostas 422 sem os dados enviados pelo cliente. O handler padrão do FastAPI devolve o
# valor recebido no campo "input" (e o corpo inteiro quando falta um campo), o que expõe
# senhas e tokens em texto puro. Aqui cada erro sai só com type, loc e msg.
from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

CAMPOS_DO_ERRO = ("type", "loc", "msg")


async def validacao_sem_dados_enviados(
    requisicao: Request, erro: RequestValidationError
) -> JSONResponse:
    erros = [
        {campo: item[campo] for campo in CAMPOS_DO_ERRO if campo in item}
        for item in erro.errors()
    ]
    # Mesmo status e formato do handler padrão: {"detail": [...]}
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": jsonable_encoder(erros)},
    )
