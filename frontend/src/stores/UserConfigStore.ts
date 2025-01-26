import { create } from 'zustand';
import updateUserConfig, { UserMeType, UserConfigType } from '../api/actions/updateUserConfig';

interface UserConfigState {
  userConfig: UserMeType;
  setUserConfig: (userConfig: UserMeType) => void;
  setPartialConfig: (userConfig: Partial<UserConfigType>) => void;
}

export const useUserConfigStore = create<UserConfigState>(set => ({
  userConfig: {
    id: 0,
    name: '',
    is_superuser: false,
    is_staff: false,
    groups: [],
    user_permissions: [],
    last_login: '',
    config: {
      stylesheet: 'dark.css',
      page_size: 12,
      sort_by: 'published',
      sort_order: 'desc',
      view_style_home: 'grid',
      view_style_channel: 'list',
      view_style_downloads: 'list',
      view_style_playlist: 'grid',
      grid_items: 3,
      hide_watched: false,
      show_ignored_only: false,
      show_subed_only: false,
      show_help_text: true,
    },
  },
  setUserConfig: userConfig => set({ userConfig }),

  setPartialConfig: async (userConfig: Partial<UserConfigType>) => {
    const userConfigResponse = await updateUserConfig(userConfig);
    set(state => ({
      userConfig: state.userConfig
        ? { ...state.userConfig, config: userConfigResponse }
        : state.userConfig,
    }));
  },
}));
