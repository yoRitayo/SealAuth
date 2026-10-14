import { useState } from "react";
import { Link } from "react-router-dom";
import { AuthCard } from "../../style/auth/AuthCard";
import { AuthLogo } from "../../style/auth/AuthLogo";
import { Button } from "../../style/componentes/button";
import { Input } from "../../style/componentes/input";
import { Label } from "../../style/componentes/label";
import { emailSchema, ValidadorDeSenha } from "../utils";

interface RegistrarPageProps {
  comRegistroBemSucedido: () => void;
}

export function Registrar({ comRegistroBemSucedido }: RegistrarPageProps) {
  const [dadosFormulario, setDadosFormulario] = useState({
    nomeCompleto: "",
    email: "",
    celular: "",
    senha: "",
    confirmarSenha: "",
  });
  const [estaCarregando, setEstaCarregando] = useState(false);
  const [erroEmailouSenha, setErroEmailouSenha] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    
    const novosDados = { ...dadosFormulario, [name]: value };
    setDadosFormulario(novosDados);

    if (name === "senha") {
      const resultado = ValidadorDeSenha.validar(value);
      setErroEmailouSenha(resultado.eValida ? "" : (resultado.erro || ""));
    }

    if (name === "confirmarSenha" || name === "senha") {
      if (novosDados.confirmarSenha && novosDados.senha !== novosDados.confirmarSenha) {
        setErroEmailouSenha("Senhas não são iguais. Tente novamente.");
      }
    }
  };

  const handleSubmissao = (e: React.SubmitEvent) => {
    e.preventDefault();

    const resultadoValidacaoEmail = emailSchema.safeParse(dadosFormulario.email);
    const resultadoValidacaoSenha = ValidadorDeSenha.validar(dadosFormulario.senha);

    if (!resultadoValidacaoSenha.eValida || !resultadoValidacaoEmail.success) {
      setErroEmailouSenha("E-mail ou senha inválidos.");
      return;
    }

    if (dadosFormulario.senha !== dadosFormulario.confirmarSenha) {
      setErroEmailouSenha("Senhas não são iguais. Tente novamente.");
      return;
    }

    setErroEmailouSenha("");
    setEstaCarregando(true);

    setTimeout(() => {
      setEstaCarregando(false);
      comRegistroBemSucedido();
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-6xl grid lg:grid-cols-2 gap-8 lg:gap-12 items-center">
        {/* Lado esquerdo - Mensagem de boas-vindas */}
        <div className="hidden lg:flex flex-col justify-center space-y-6 px-8">
          <div className="space-y-4">
            <h1 className="text-2xl font-semibold text-gray-800">
              Junte-se ao nosso espaço seguro 
            </h1>
            <p className="text-xl text-gray-600 leading-relaxed">
              Crie sua conta
            </p>
          </div>
          <div className="space-y-4 pt-8">
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0 mt-1">
                <svg
                  className="w-4 h-4 text-purple-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div>
                <h3 className="font-medium text-gray-900">
                  Hasheamento com Argon2id
                </h3>
                <p className="text-sm text-gray-600">
                  Vencedor da Password Hashing Competition e recomendado pela OWASP
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0 mt-1">
                <svg
                  className="w-4 h-4 text-purple-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div>
                <h3 className="font-medium text-gray-900">
                  Autenticação com JWT
                </h3>
                <p className="text-sm text-gray-600">
                  Gerenciamento seguro de sessão através de tempo configurado por você.
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0 mt-1">
                <svg
                  className="w-4 h-4 text-purple-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div>
                <h3 className="font-medium text-gray-900">
                  Comunicação criptografada 
                </h3>
                <p className="text-sm text-gray-600">
                  Tráfego ocorre sobre HTTPS com TLS 1.2 ou 1.3 
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0 mt-1">
                <svg
                  className="w-4 h-4 text-purple-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div>
                <h3 className="font-medium text-gray-900">
                  Auditoria à prova de adulteração
                </h3>
                <p className="text-sm text-gray-600">
                  Inserção administrar por mecanismo advisory lock do PostgreSQL
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Lado direito - Formulário de registro */}
        <div className="flex justify-center">
          <div className="w-full max-w-[480px]">
            <div className="lg:hidden mb-8">
              <AuthLogo />
            </div>
            <AuthCard
              title="Criar conta"
              subtitle="Preencha seus dados para começar"
            >
              <form
                onSubmit={handleSubmissao}
                className="space-y-5"
              >
                {/* Nome completo */}
                <div className="space-y-2">
                  <Label htmlFor="nomeCompleto">Nome completo</Label>
                  <Input
                    id="nomeCompleto"
                    name="nomeCompleto"
                    type="text"
                    placeholder="João da Silva"
                    value={dadosFormulario.nomeCompleto}
                    onChange={handleChange}
                    required
                    className="h-12 rounded-xl"
                  />
                </div>

                {/* E-mail */}
                <div className="space-y-2">
                  <Label htmlFor="email">Endereço de e-mail</Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="voce@exemplo.com"
                    value={dadosFormulario.email}
                    onChange={handleChange}
                    required
                    className="h-12 rounded-xl"
                  />
                </div>

                {/* Celular */}
                <div className="space-y-2">
                  <Label htmlFor="celular">Número de celular</Label>
                  <Input
                    id="celular"
                    name="celular"
                    type="tel"
                    placeholder="+55 (11) 00000-0000"
                    value={dadosFormulario.celular}
                    onChange={handleChange}
                    required
                    className="h-12 rounded-xl"
                  />
                </div>

                {/* Senha */}
                <div className="space-y-2">
                  <Label htmlFor="senha">Senha</Label>
                  <Input
                    id="senha"
                    name="senha"
                    type="password"
                    placeholder="Digite uma senha segura"
                    value={dadosFormulario.senha}
                    onChange={handleChange}
                    required
                    className={`h-12 rounded-xl ${erroEmailouSenha ? "border-red-500" : ""}`}
                  />
                </div>

                {/* Confirmar senha */}
                <div className="space-y-2">
                  <Label htmlFor="confirmarSenha">
                    Confirmar senha
                  </Label>
                  <Input
                    id="confirmarSenha"
                    name="confirmarSenha"
                    type="password"
                    placeholder="*******"
                    value={dadosFormulario.confirmarSenha}
                    onChange={handleChange}
                    required
                    className={`h-12 rounded-xl ${erroEmailouSenha ? "border-red-500" : ""}`}
                  />
                  {erroEmailouSenha && (
                    <p className="text-sm text-red-600">
                      {erroEmailouSenha}
                    </p>
                  )}
                </div>

                {/* Botão de criar conta */}
                <Button
                  type="submit"
                  className="w-full h-12 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 transition-all duration-200"
                  disabled={estaCarregando}
                >
                  {estaCarregando
                    ? "Criando conta..."
                    : "Criar conta"}
                </Button>

                {/* Link para login */}
                <div className="text-center pt-4">
                  <p className="text-sm text-gray-600">
                    Já tem uma conta?{" "}
                    <Link
                      to="/"
                      className="text-purple-600 hover:text-purple-700 font-medium transition-colors"
                    >
                      Entrar
                    </Link>
                  </p>
                </div>
              </form>
            </AuthCard>
          </div>
        </div>
      </div>
    </div>
  );
}