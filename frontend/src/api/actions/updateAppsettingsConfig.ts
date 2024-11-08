import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';
import { AppSettingsConfigType } from '../loader/loadAppsettingsConfig';

type ObjectType = Record<
  string,
  string | number | boolean | Record<string, string | number | boolean>
>;

function flattenObject(ob: ObjectType) {
  // source: https://stackoverflow.com/a/53739792
  const toReturn: ObjectType = {};

  for (const i in ob) {
    if (!Object.prototype.hasOwnProperty.call(ob, i)) continue;

    if (typeof ob[i] == 'object' && ob[i] !== null) {
      const flatObject = flattenObject(ob[i]);
      for (const x in flatObject) {
        if (!Object.prototype.hasOwnProperty.call(flatObject, x)) continue;

        toReturn[i + '.' + x] = flatObject[x];
      }
    } else {
      toReturn[i] = ob[i];
    }
  }

  return toReturn;
}

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
    body: JSON.stringify(flattenObject(config)),
  });

  const appSettingsConfig = await response.json();
  console.log('updateAppsettingsConfig', appSettingsConfig);

  return appSettingsConfig;
};

export default updateAppsettingsConfig;
