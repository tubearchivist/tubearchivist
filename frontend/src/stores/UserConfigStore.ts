import { create } from 'zustand';
import updateUserConfig, { UserMeType, UserConfigType } from '../api/actions/updateUserConfig';

interface UserConfigState {
  userConfig: UserMeType | null;
  setUserConfig: (userConfig: UserMeType) => void;
  updateUserConfig: (updates: UserConfigType) => void;
}

export const useUserConfigStore = create<UserConfigState>((set) => ({

  userConfig: null,
  setUserConfig: (userConfig) => set({ userConfig }),

  updateUserConfig: async (updates: UserConfigType) => {
    const userConfigResponse = await updateUserConfig(updates);
    set((state) => ({
      userConfig: state.userConfig ? { ...state.userConfig, config: userConfigResponse } : state.userConfig,
    }));
  }

}))
