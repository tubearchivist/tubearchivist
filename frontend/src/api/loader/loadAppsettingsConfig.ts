import APIClient from '../../functions/APIClient';

export type AppSettingsConfigType = {
  subscriptions: {
    channel_size: number | null;
    live_channel_size: number | null;
    shorts_channel_size: number | null;
    auto_start: boolean;
  };
  downloads: {
    limit_speed: number | null;
    sleep_interval: number | null;
    autodelete_days: number | null;
    format: string | null;
    format_sort: string | null;
    add_metadata: boolean;
    add_thumbnail: boolean;
    subtitle: string | null;
    subtitle_source: string | null;
    subtitle_index: boolean;
    comment_max: string | null;
    comment_sort: string;
    cookie_import: boolean;
    potoken: boolean;
    throttledratelimit: number | null;
    extractor_lang: string | null;
    integrate_ryd: boolean;
    integrate_sponsorblock: boolean;
  };
  application: {
    enable_snapshot: boolean;
  };
};

const loadAppsettingsConfig = async (): Promise<AppSettingsConfigType> => {
  return APIClient('/api/appsettings/config/');
};

export default loadAppsettingsConfig;
