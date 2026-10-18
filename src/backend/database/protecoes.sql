-- Executado pelo app logo após o create_all, como guardiao_app (admin).
-- __APP_USUARIO__ é substituído pelo nome do usuário da aplicação (BANCO_APP_USUARIO).

-- Logs e tentativas não têm FK para USUARIOS: o id fica gravado após a exclusão do usuário.
-- DROP IF EXISTS: bancos criados antes dessa regra ainda têm a constraint.
ALTER TABLE "LOGS_AUDITORIA" DROP CONSTRAINT IF EXISTS "LOGS_AUDITORIA_id_usuario_fkey";
ALTER TABLE "TENTATIVAS_LOGIN" DROP CONSTRAINT IF EXISTS "TENTATIVAS_LOGIN_id_usuario_fkey";

-- Logs de auditoria e tentativas de login: o app só insere e lê
REVOKE UPDATE, DELETE, TRUNCATE ON "LOGS_AUDITORIA", "TENTATIVAS_LOGIN" FROM __APP_USUARIO__;

-- Segunda camada: o banco recusa qualquer alteração nos logs, mesmo para o admin
CREATE OR REPLACE FUNCTION bloqueia_alteracao() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'tabela somente insercao';
END; $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS logs_imutaveis ON "LOGS_AUDITORIA";
CREATE TRIGGER logs_imutaveis
    BEFORE UPDATE OR DELETE ON "LOGS_AUDITORIA"
    FOR EACH ROW EXECUTE FUNCTION bloqueia_alteracao();
