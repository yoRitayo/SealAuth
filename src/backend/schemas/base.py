from pydantic import BaseModel, ConfigDict


class Entidade(BaseModel):
    # Permite montar o schema a partir do objeto ORM
    model_config = ConfigDict(from_attributes=True)
