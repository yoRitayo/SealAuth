import type { Usuario, UsuarioDTO } from './usuario';

export interface RequisicaoLogin {
    email: string;
    senha: string;
}

export interface RespostaRequisicaoLogin {
    usuario: UsuarioDTO;
    token: string;
}

export interface EstadoAutenticacao {
    usuario: Usuario | null;
    token: string | null;
    estaCarregando: boolean;
}

