export function AuthLogo() {
  return (
    <div className="flex items-center justify-center gap-2 mb-8">
      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg">
          <img src="/seal-icon72.png" alt="Ícone do SealAuth" className="block"/>
      </div>
      <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
        SealAuth
      </span>
    </div>
  );
}
