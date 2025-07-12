import { create } from 'zustand';
import { AppSettingsConfigType } from '../api/loader/loadAppsettingsConfig';

interface AppSettingsState {
  appSettingsConfig: AppSettingsConfigType;
  setAppSettingsConfig: (appSettingsConfig: AppSettingsConfigType) => void;
}

export const useAppSettingsStore = create<AppSettingsState>(set => ({
  appSettingsConfig: {
    subscriptions: {
      channel_size: null,
      live_channel_size: null,
      shorts_channel_size: null,
      playlist_size: null,
      auto_start: false,
      extract_flat: false,
    },
    downloads: {
      limit_speed: null,
      sleep_interval: null,
      autodelete_days: null,
      format: null,
      format_sort: null,
      add_metadata: false,
      add_thumbnail: false,
      subtitle: null,
      subtitle_source: null,
      subtitle_index: false,
      comment_max: null,
      comment_sort: 'asc',
      cookie_import: false,
      potoken: false,
      throttledratelimit: null,
      extractor_lang: null,
      integrate_ryd: false,
      integrate_sponsorblock: false,
    },
    application: {
      enable_snapshot: false,
      enable_cast: false,
    },
  },
  setAppSettingsConfig: appSettingsConfig => set({ appSettingsConfig }),
}));
