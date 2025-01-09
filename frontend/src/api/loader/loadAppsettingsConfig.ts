import APIClient from '../../functions/APIClient';

export type AppSettingsConfigType = {
  subscriptions: {
    channel_size: number;
    live_channel_size: number;
    shorts_channel_size: number;
    auto_start: boolean;
  };
  downloads: {
    limit_speed: number | undefined;
    sleep_interval: number;
    autodelete_days: number;
    format: string | undefined;
    format_sort: string | undefined;
    add_metadata: boolean;
    add_thumbnail: boolean;
    subtitle: string | undefined;
    subtitle_source: boolean | string;
    subtitle_index: boolean;
    comment_max: string | undefined;
    comment_sort: string;
    cookie_import: boolean;
    throttledratelimit: number | undefined;
    extractor_lang: string | undefined;
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
