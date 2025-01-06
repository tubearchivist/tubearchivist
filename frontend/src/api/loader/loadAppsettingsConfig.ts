import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

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
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/appsettings/config/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const appSettingsConfig = await response.json();

  if (isDevEnvironment()) {
    console.log('loadApplicationConfig', appSettingsConfig);
  }

  return appSettingsConfig;
};

export default loadAppsettingsConfig;
