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

interface RegistrationSuccessModalProps {
  open: boolean;
  onClose: () => void;
}

export function RegistrationSuccessModal({ open, onClose }: RegistrationSuccessModalProps) {
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
            Welcome Aboard! 🎉
          </DialogTitle>
          <DialogDescription className="text-center pt-2">
            Your account has been successfully created. You're now ready to explore amazing gadgets and exclusive deals!
          </DialogDescription>
        </DialogHeader>
        
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-xl p-4 my-4 space-y-2">
          <p className="text-sm font-medium text-purple-900">
            🎁 Welcome Bonus Unlocked!
          </p>
          <p className="text-sm text-purple-700">
            You've received a 10% discount coupon for your first purchase.
          </p>
        </div>

        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
            <span>Account verified and activated</span>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
            <span>Welcome email sent to your inbox</span>
          </div>
          <div className="flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
            <span>Special offers and updates enabled</span>
          </div>
        </div>

        <DialogFooter className="sm:justify-center gap-2 pt-4">
          <Button
            onClick={handleContinue}
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-xl"
          >
            Continue to Login
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}