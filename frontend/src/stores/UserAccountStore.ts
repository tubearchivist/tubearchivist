import { create } from 'zustand';
import { UserAccountType } from '../api/loader/loadUserAccount';

interface AccountState {
  userAccount: UserAccountType | null;
  setUserAccount: (userAccount: UserAccountType) => void;
}

export const useUserAccountStore = create<AccountState>(set => ({
  userAccount: null,
  setUserAccount: userAccount => set({ userAccount }),
}));
