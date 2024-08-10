import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';
import { AppSettingsConfigType } from '../loader/loadAppsettingsConfig';

const updateAppsettingsConfig = async (config: AppSettingsConfigType) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/appsettings/config/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),
    body: JSON.stringify(config),
  });

  const appSettingsConfig = await response.json();
  console.log('updateAppsettingsConfig', appSettingsConfig);

  return appSettingsConfig;
};

export default updateAppsettingsConfig;
