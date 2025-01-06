import { create } from 'zustand';
import { AuthenticationType } from '../pages/Base';

interface AuthState {
  auth: AuthenticationType | null;
  setAuth: (auth: AuthenticationType) => void;
}

export const useAuthStore = create<AuthState>(set => ({
  auth: null,
  setAuth: auth => set({ auth }),
}));
