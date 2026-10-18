/** ROLE-BASED ACESS CONTROL (RBAC) — espelha controle_acesso.py do backend **/

import type { Papel, Permissao } from '../types/user-types';

export const PERMISSOES: Record<Papel, ReadonlyArray<Permissao>> = {
  admin: ['ler_perfil', 'ler_logs', 'ler_alertas', 'gerenciar_usuarios', 'gerenciar_bloqueios'],
  analista: ['ler_perfil', 'ler_logs', 'ler_alertas'],
  usuario: ['ler_perfil'],
};

export function temPermissao(papel: Papel, permissao: Permissao): boolean {
  return PERMISSOES[papel]?.includes(permissao) ?? false;
}
