import { z } from 'zod';

export const emailSchema = z.email({ message: "Endereço de e-mail inválido" });
export type Email = z.infer<typeof emailSchema>;

export class ValidadorDeSenha {
    // Escrito com base em regras do NIST (National Institute of Standards and Technology) e no https://www.altftool.com/tools/all/regex-library-passwords

    // Lista de senhas impedidas de serem utilizadas pelo usuário 
    private static readonly SENHAS_IMPEDIDAS = new Set([
                "12345678", "123456789", "1234567890", "00000000", "11111111", "87654321",
                "qwertyuiop", "asdfghjkl", "zxcvbnm1", "qwerty1234", "qwertyui",
                "password", "password123", "administrator", "password1", "welcome1", 
                "iloveyou", "sunshine", "princess", "football", "superman",
                "senha123", "senha1234", "mudar123", "mudar1234", "administrador",
                "usuario123", "bemvindo", "bemvindo123", "deusereirei", "brasil123",
                "admin123"
    ]);


    public static validar(senha: string): { eValida: boolean; erro?: string } {
        const regexSenhaDesejada = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/

        // Proibir caracteres idênticos repetidos mais de uma vez consecutiva
        const regexCaracteresRepetidos = /^(?!.*(.)\1{3,}).*$/;

        if (senha.length > 64) {
            return { eValida: false, erro: "A senha não deve exceder 64 caracteres." };
        }

        if (!regexCaracteresRepetidos.test(senha)) {
            return { eValida: false, erro: "A senha não pode conter caracteres idênticos repetidos consecutivamente." };
        } 

        // Inclui o espaço 
        if (!regexSenhaDesejada.test(senha)){
            return { eValida: false, erro: "A senha deve ter no mínimo 8 caracteres, com letras maiúscula/minúscula, 1 dígito e ao menos um símbolo especial" };
        }

        if (this.SENHAS_IMPEDIDAS.has(senha.toLowerCase().trim())) {
            return { eValida: false, erro: "Esta senha é muito comum ou foi vazada. Escolha outra." };
        }

        return { eValida: true };
    }
}