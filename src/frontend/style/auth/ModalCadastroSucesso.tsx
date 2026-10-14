import { CheckCircle2, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../componentes/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../componentes/dialog';

interface ModalCadastroSucessoProps {
  open: boolean;
  onClose: () => void;
}

export function ModalCadastroSucesso({ open, onClose }: ModalCadastroSucessoProps) {
  const navigate = useNavigate();

  const handleContinue = () => {
    onClose();
    void navigate('/');
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md rounded-2xl">
        <DialogHeader>
          <div className="flex justify-center mb-4 relative">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-green-100 to-emerald-100 flex items-center justify-center relative">
              <CheckCircle2 className="w-10 h-10 text-green-600" />
              <Sparkles className="w-5 h-5 text-yellow-500 absolute -top-1 -right-1 animate-pulse" />
            </div>
          </div>
          <DialogTitle className="text-center text-2xl">
            Bem-vindo.
          </DialogTitle>
          <DialogDescription className="text-center pt-2">
            Sua conta foi criada com sucesso. Você está pronto para aproveitar de seu sistema de autenticação seguro. 
          </DialogDescription>
        </DialogHeader>

        <DialogFooter className="sm:justify-center gap-2 pt-4">
          <Button
            onClick={handleContinue}
            className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 transition-all duration-200 rounded-xl"
          >
            Continue to Login
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}