import { useState } from "react";
import { Link } from "react-router-dom";
import { AuthCard } from "../../style/auth/AuthCard";
import { AuthLogo } from "../../style/auth/AuthLogo";
import { Button } from "../../style/componentes/button";
import { Input } from "../../style/componentes/input";
import { Label } from "../../style/componentes/label";

interface RegistrarPageProps {
  comRegistroBemSucedido: () => void;
}

export function Registrar({comRegistroBemSucedido,}: RegistrarPageProps) {
  const [dadosFormulario, setdadosFormulario] = useState({
    nomeCompleto: "",
    email: "",
    celular: "",
    senha: "",
    confirmarSenha: "",
  });
  const [estaCarregando, setEstaCarregando] = useState(false);
  const [senhaError, setsenhaError] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>, ) => {
    const { name, value } = e.target;
    setdadosFormulario((prev) => ({ ...prev, [name]: value }));

    // Limpar erro de senha quando usuário digita
    if (name === "senha" || name === "confirmarSenha") {
      setsenhaError("");
    }
  };

  const handleSubmissao = (e: React.SubmitEvent) => {
    e.preventDefault();

    if (dadosFormulario.senha !== dadosFormulario.confirmarSenha) {
      setsenhaError("Senhas não são iguais. Tente novamente.");
      return;
    }

    setEstaCarregando(true);

    // Simular registro
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
            <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              Junte-se à nossa loja
            </h1>
            <p className="text-xl text-gray-600 leading-relaxed">
              Crie sua conta e tenha acesso a ofertas exclusivas
              nos últimos gadgets e tecnologias.
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
                  Ofertas exclusivas
                </h3>
                <p className="text-sm text-gray-600">
                  Descontos exclusivos para membros em gadgets premium
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
                  Envio rápido
                </h3>
                <p className="text-sm text-gray-600">
                  Entrega expressa grátis em todos os pedidos
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
                  Proteção de garantia
                </h3>
                <p className="text-sm text-gray-600">
                  Garantia estendida em todos os produtos
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
                    placeholder="••••••••"
                    value={dadosFormulario.senha}
                    onChange={handleChange}
                    required
                    className="h-12 rounded-xl"
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
                    className={`h-12 rounded-xl ${senhaError ? "border-red-500" : ""}`}
                  />
                  {senhaError && (
                    <p className="text-sm text-red-600">
                      {senhaError}
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