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

-- Blind index do e-mail (HMAC-SHA256): create_all não adiciona colunas a tabelas existentes
ALTER TABLE "USUARIOS" ADD COLUMN IF NOT EXISTS email_indice bytea;
CREATE INDEX IF NOT EXISTS "ix_USUARIOS_email_indice" ON "USUARIOS" (email_indice);

-- IDS/IPS: alerta só por IP, tentativa de usuário inexistente e bloqueio de IP sem expiração
ALTER TABLE "ALERTAS" ALTER COLUMN id_usuario DROP NOT NULL;
ALTER TABLE "TENTATIVAS_LOGIN" ALTER COLUMN id_usuario DROP NOT NULL;
ALTER TABLE "BLOQUEIOS_IP" ALTER COLUMN expira_em DROP NOT NULL;

-- Excluir o usuário não apaga os alertas dele (evidência do IDS)
ALTER TABLE "ALERTAS" DROP CONSTRAINT IF EXISTS "ALERTAS_id_usuario_fkey";
ALTER TABLE "ALERTAS" ADD CONSTRAINT "ALERTAS_id_usuario_fkey"
    FOREIGN KEY (id_usuario) REFERENCES "USUARIOS" (id) ON DELETE SET NULL;

-- Janelas do IDS: tentativas de um IP em ordem de tempo
CREATE INDEX IF NOT EXISTS "ix_TENTATIVAS_LOGIN_ip_atualizado_em"
    ON "TENTATIVAS_LOGIN" (ip, atualizado_em);
