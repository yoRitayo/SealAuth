import { AlertCircle } from 'lucide-react';
import { Button } from '../componentes/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '../componentes/dialog';

interface LoginErrorModalProps {
  open: boolean;
  onClose: () => void;
}

export function LoginErrorModal({ open, onClose }: LoginErrorModalProps) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md rounded-2xl">
        <DialogHeader>
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-red-600" />
            </div>
          </div>
          <DialogTitle className="text-center text-2xl">Login Failed</DialogTitle>
          <DialogDescription className="text-center pt-2">
            The email or senha you entered is incorrect. Please check your credentials and try again.
          </DialogDescription>
        </DialogHeader>
        
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 my-4">
          <p className="text-sm text-red-800">
            <strong>Error Code:</strong> AUTH_INVALID_CREDENTIALS
          </p>
        </div>

        <DialogFooter className="sm:justify-center gap-2">
          <Button
            onClick={onClose}
            className="w-full sm:w-auto bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 rounded-xl"
          >
            Try Again
          </Button>
          <Button
            variant="outline"
            onClick={onClose}
            className="w-full sm:w-auto rounded-xl"
          >
            Reset senha
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
