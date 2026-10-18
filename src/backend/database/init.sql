-- Executado na criação do volume do Postgres, como superusuário (guardiao_app).
-- Cria a extensão, o usuário restrito da aplicação e as permissões padrão das tabelas futuras.

\getenv admin_usuario POSTGRES_USER
\getenv app_usuario BANCO_APP_USUARIO
\getenv app_senha BANCO_APP_SENHA

CREATE EXTENSION IF NOT EXISTS citext;

CREATE ROLE :"app_usuario" LOGIN PASSWORD :'app_senha';
GRANT USAGE ON SCHEMA public TO :"app_usuario";

-- Tabelas e sequências criadas pelo admin já nascem com as permissões do app
ALTER DEFAULT PRIVILEGES FOR ROLE :"admin_usuario" IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"app_usuario";
ALTER DEFAULT PRIVILEGES FOR ROLE :"admin_usuario" IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO :"app_usuario";
