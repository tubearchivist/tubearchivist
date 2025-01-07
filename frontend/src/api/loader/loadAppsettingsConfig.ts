import APIClient from '../../functions/APIClient';

export type AppSettingsConfigType = {
  subscriptions: {
    channel_size: number;
    live_channel_size: number;
    shorts_channel_size: number;
    auto_start: boolean;
  };
  downloads: {
    limit_speed: false | number;
    sleep_interval: number;
    autodelete_days: number;
    format: number | string;
    format_sort: boolean | string;
    add_metadata: boolean;
    add_thumbnail: boolean;
    subtitle: boolean | string;
    subtitle_source: boolean | string;
    subtitle_index: boolean;
    comment_max: string | number;
    comment_sort: string;
    cookie_import: boolean;
    throttledratelimit: false | number;
    extractor_lang: boolean | string;
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
