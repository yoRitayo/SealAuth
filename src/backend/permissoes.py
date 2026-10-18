# Mapeamento RBAC
PERMISSOES: dict[str, frozenset[str]] = {
    "admin": frozenset({"ler_perfil", "ler_logs", "ler_alertas", "gerenciar_usuarios", "gerenciar_bloqueios"}),
    "analista": frozenset({"ler_perfil", "ler_logs", "ler_alertas"}),
    "usuario": frozenset({"ler_perfil"}),
}
