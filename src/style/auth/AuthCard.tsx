import type { ReactNode } from 'react';

interface AuthCardProps {
  children: ReactNode;
  title: string;
  subtitle?: string;
}

export function AuthCard({ children, title, subtitle }: AuthCardProps) {
  return (
    <div className="w-full max-w-[480px] bg-white rounded-2xl shadow-2xl shadow-black/10 p-6 sm:p-8 md:p-10">
      <div className="text-center mb-6 md:mb-8">
        <h1 className="text-2xl sm:text-3xl font-semibold text-gray-900 mb-2">{title}</h1>
        {subtitle && (
          <p className="text-sm text-gray-600">{subtitle}</p>
        )}
      </div>
      {children}
    </div>
  );
}