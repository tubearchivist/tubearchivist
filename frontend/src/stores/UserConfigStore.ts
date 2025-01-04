import { create } from 'zustand';
import updateUserConfig, { UserMeType, UserConfigType } from '../api/actions/updateUserConfig';

interface UserConfigState {
  userConfig: UserMeType;
  setUserConfig: (userConfig: UserMeType) => void;
  updateUserConfig: (updates: UserConfigType) => void;
}

export const useUserConfigStore = create<UserConfigState>((set) => ({

  userConfig: {
    id: 0,
    name: '',
    is_superuser: false,
    is_staff: false,
    groups: [],
    user_permissions: [],
    last_login: '',
    config: {}
  },
  setUserConfig: (userConfig) => set({ userConfig }),

  updateUserConfig: async (updates: UserConfigType) => {
    const userConfigResponse = await updateUserConfig(updates);
    set((state) => ({
      userConfig: state.userConfig ? { ...state.userConfig, config: userConfigResponse } : state.userConfig,
    }));
  }

}))
