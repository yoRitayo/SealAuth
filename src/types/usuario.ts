export interface UsuarioDTO {
    id: string;
    nomeCompleto: string;
    celular: string;
    email: string;
    nomeUsuario: string;
    tipo: 'admin' | 'padrao' | 'visitante'
    criadoEm: string;
    atualizadoEm: string;
}

export interface Usuario {
    id: string;
    nomeCompleto: string;
    celular: string;
    email: string;
    nomeUsuario: string;
    tipo: 'admin' | 'padrao' | 'visitante'
    criadoEm: string;
    atualizadoEm: Date;
}