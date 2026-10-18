export type Permissao =
  | 'ler_perfil'
  | 'ler_logs'
  | 'ler_alertas'
  | 'gerenciar_usuarios'
  | 'gerenciar_bloqueios';

export type Papel = 'admin' | 'analista' | 'usuario';

// Alinhado ao backend (schemas/usuario.py): "pendente" até o e-mail ser confirmado
export type Status = 'pendente' | 'ativo' | 'bloqueado';

export interface Usuario {
  id: string;
  nome_usuario: string;
  papel: Papel;
  status: Status;
  falhas_consecutivas: number;
  bloqueado_ate: string | null;
  criado_em: string;
}
