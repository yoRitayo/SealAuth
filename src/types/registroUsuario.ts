import type { Usuario, UsuarioDTO } from './usuario';

export interface RequisicaoRegistro {
    usuario: UsuarioDTO;
    senha: string;
}

export interface RespostaRequisicaoRegistro {
    usuario: Usuario;
}

export interface EstadoRegistro {
    usuario: Usuario | null;
    senha: string;
    confirmarSenha: string;
}

