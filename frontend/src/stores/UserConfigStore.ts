import { create } from 'zustand';
import { UserConfigType } from '../api/actions/updateUserConfig';

interface UserConfigState {
  userConfig: UserConfigType;
  setUserConfig: (userConfig: UserConfigType) => void;
}

export const useUserConfigStore = create<UserConfigState>(set => ({
  userConfig: {
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
    file_size_unit: 'binary',
    show_ignored_only: false,
    show_subed_only: false,
    show_help_text: true,
  },
  setUserConfig: userConfig => set({ userConfig }),
}));
