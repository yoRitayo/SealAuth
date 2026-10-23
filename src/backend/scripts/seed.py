"""Script para criar usuário admin inicial no banco de dados."""
from datetime import UTC, datetime
from uuid import uuid4

from database.database import SessaoLocal
from database.entidades import Usuario
from seguranca import gerar_hash_senha


def criar_usuario_admin():
    """Cria um usuário admin padrão se não existir nenhum usuário no banco."""
    db = SessaoLocal()
    try:
        usuario_existente = db.query(Usuario).first()
        if usuario_existente:
            print("✓ Usuários já existem no banco, pulando seed")
            return

        admin = Usuario(
            id=uuid4(),
            nome_usuario="admin",
            email="admin@sealauth.local",
            email_indice=None,  # será computado ao fazer login
            senha=gerar_hash_senha("Admin@123"),
            papel="admin",
            status="ativo",
            falhas_consecutivas=0,
            bloqueado_ate=None,
            criado_em=datetime.now(UTC),
        )
        db.add(admin)
        db.commit()
        print("✓ Usuário admin criado:")
        print(f"  Usuário: {admin.nome_usuario}")
        print(f"  Email: {admin.email}")
        print(f"  Senha: Admin@123")
        print(f"  Papel: {admin.papel}")
    except Exception as e:
        db.rollback()
        print(f"✗ Erro ao criar usuário admin: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    criar_usuario_admin()
